import sys
import re
import math
import logging
from time import sleep
import traceback

# util for conversion
def num(s):
    """Convert string to number, handling various formats safely"""
    if isinstance(s, (float, int)):
        return float(s)
    if not s:
        return 0.0
    try:
        # remove any whitespace
        s = str(s).strip()
        # try integer first
        if '.' not in s and 'e' not in s.lower():
            return float(int(s))
        # fall back to float
        return float(s)
    except (ValueError, OverflowError, TypeError):
        logging.warning(f"Could not convert '{s}' to number, defaulting to 0")
        return 0.0

class Vertex:
    def __init__(self, x, y, z):
        self.x = num(x)
        self.y = num(y)
        self.z = num(z)

    def __sub__(self, other):
        return Vertex(self.x - other.x, self.y - other.y, self.z - other.z)

    def __add__(self, other):
        return Vertex(self.x + other.x, self.y + other.y, self.z + other.z)

    def cross(self, other):
        return Vertex(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def normalize(self):
        mag = self.magnitude()
        # protect against division by zero
        if mag < 1e-10:
            logging.warning("Attempting to normalize zero-length vector")
            return Vertex(0, 0, 1)
        return Vertex(self.x / mag, self.y / mag, self.z / mag)

    def scale(self, scalar):
        if abs(scalar) < 1e-10:
            logging.warning(f"Scaling by very small value: {scalar}")
        return Vertex(self.x * scalar, self.y * scalar, self.z * scalar)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def __repr__(self):
        return f"{self.x:.6f} {self.y:.6f} {self.z:.6f}"

    def __eq__(self, other):
        epsilon = 0.001
        return (isinstance(other, Vertex) and 
                abs(self.x - other.x) < epsilon and 
                abs(self.y - other.y) < epsilon and 
                abs(self.z - other.z) < epsilon)

    def __hash__(self):
        return hash((round(self.x, 3), round(self.y, 3), round(self.z, 3)))

class Side:
    def __init__(self):
        self.id = None
        self.plane = []
        self.plane_str = ''
        self.vertices_plus = []
        self.material = None
        self.uaxis = None
        self.vaxis = None
        self.rotation = None
        self.lightmapscale = None
        self.smoothing_groups = None
        self.parent_solid = None

    def parse(self, data):
        if not isinstance(data, dict):
            logging.warning(f"Invalid side data type: {type(data)}")
            return
            
        self.id = data.get('id')
        plane_str = data.get('plane', '')
        self.plane_str = plane_str
        
        # regex for plane points, handling scientific notation better now
        plane_match = re.findall(
            r'\(([^,\)]+)\s+([^,\)]+)\s+([^,\)]+)\)', 
            plane_str
        )
        
        if len(plane_match) >= 3:
            try:
                self.plane = [Vertex(coords[0], coords[1], coords[2]) 
                             for coords in plane_match[:3]]
            except Exception as e:
                logging.warning(f"Failed to parse plane coordinates: {e}")
                self.plane = []
        
        # parse vertices_plus if available
        vertices_plus_data = data.get('vertices_plus', {})
        if vertices_plus_data:
            vertices_list = vertices_plus_data.get('v', [])
            if not isinstance(vertices_list, list):
                vertices_list = [vertices_list]
            
            for vertex_str in vertices_list:
                try:
                    coords = vertex_str.strip().split()
                    if len(coords) == 3:
                        self.vertices_plus.append(Vertex(coords[0], coords[1], coords[2]))
                except Exception as e:
                    logging.warning(f"Failed to parse vertex: {vertex_str}, error: {e}")
        
        self.material = data.get('material')
        self.uaxis = data.get('uaxis')
        self.vaxis = data.get('vaxis')
        self.rotation = data.get('rotation')
        self.lightmapscale = data.get('lightmapscale')
        self.smoothing_groups = data.get('smoothing_groups')

    def get_face_center(self):
        """Calculate the center point of this face"""
        vertices = self.get_vertices()
        if not vertices:
            return None
        
        center = Vertex(0, 0, 0)
        for v in vertices:
            center = center + v
        return center.scale(1.0 / len(vertices))

    def compute_normal(self):
        """Compute the outward-facing normal of this face"""
        # try vertices_plus first if available (more accurate)
        points_to_use = self.vertices_plus if len(self.vertices_plus) >= 3 else self.plane
        
        if len(points_to_use) < 3:
            return None
        
        try:
            # for triangular faces
            if len(points_to_use) == 3:
                p1, p2, p3 = points_to_use[0], points_to_use[1], points_to_use[2]
                v1 = p2 - p1
                v2 = p3 - p1
                normal = v1.cross(v2).normalize()
            else:
                # for quad or more vertices, use newell's method
                normal = Vertex(0, 0, 0)
                n = len(points_to_use)
                for i in range(n):
                    v1 = points_to_use[i]
                    v2 = points_to_use[(i + 1) % n]
                    normal.x += (v1.y - v2.y) * (v1.z + v2.z)
                    normal.y += (v1.z - v2.z) * (v1.x + v2.x)
                    normal.z += (v1.x - v2.x) * (v1.y + v2.y)
                normal = normal.normalize()
            
            # verify normal direction using face center and solid bounds
            if self.parent_solid:
                face_center = self.get_face_center()
                solid_center = self.parent_solid.get_approximate_center()
                if face_center and solid_center:
                    to_face = face_center - solid_center
                    # flip if clearly pointing wrong direction
                    if normal.dot(to_face) < -0.1:
                        normal = normal.scale(-1)
            
            return normal
        except Exception as e:
            logging.warning(f"Failed to compute normal: {e}")
            return None

    def get_vertices(self):
        """Get the actual vertices of this face"""
        if self.vertices_plus:
            return self.vertices_plus
        return self.plane[:3] if len(self.plane) >= 3 else []

    def is_planar(self, tolerance=0.1):
        """Check if face is planar within tolerance"""
        vertices = self.get_vertices()
        if len(vertices) <= 3:
            return True
        
        normal = self.compute_normal()
        if not normal:
            return False
        
        # check if all vertices lie on the same plane
        p0 = vertices[0]
        for v in vertices[3:]:
            vec_to_v = v - p0
            distance_from_plane = abs(vec_to_v.dot(normal))
            if distance_from_plane > tolerance:
                return False
        
        return True

    def is_surfable(self):
        """Check if this surface is surfable (not a pure vertical wall)"""
        normal = self.compute_normal()
        if normal is None:
            return False
        
        # a surface is surfable if it has any significant z component
        return abs(normal.z) > 0.01

    def get_surface_type(self):
        """Classify the surface type with improved slope detection"""
        normal = self.compute_normal()
        if normal is None:
            return "unknown"
        
        z = abs(normal.z)
        
        # thresholds for detection
        if z < 0.01:  # nearly vertical
            return "wall"
        elif z >= 0.985:  # nearly horizontal
            return "floor" if normal.z > 0 else "ceiling"
        elif z >= 0.7:  # steep but surfable
            return "steep_slope" if normal.z > 0 else "steep_ceiling_slope"
        elif z >= 0.3:  # moderate ramp
            return "ramp" if normal.z > 0 else "ceiling_ramp"
        else:  # gentle slope
            return "gentle_slope" if normal.z > 0 else "gentle_ceiling_slope"

    def get_angle_from_horizontal(self):
        """Get the angle of this surface from horizontal in degrees"""
        normal = self.compute_normal()
        if normal is None:
            return None
        
        # angle from horizontal is arcsin of |normal.z|
        z_abs = min(1.0, abs(normal.z))
        return math.degrees(math.asin(z_abs))

class Solid:
    def __init__(self):
        self.id = None
        self.sides = []
        self.editor = {}

    def parse(self, data):
        if not isinstance(data, dict):
            logging.warning(f"Invalid solid data type: {type(data)}")
            return
            
        self.id = data.get('id')
        sides_data = data.get('side', [])
        if not isinstance(sides_data, list):
            sides_data = [sides_data]
        
        for side_data in sides_data:
            side = Side()
            side.parse(side_data)
            side.parent_solid = self
            self.sides.append(side)
        
        self.editor = data.get('editor', {})

    def get_approximate_center(self):
        """Get approximate center of the solid using all vertices"""
        all_vertices = []
        for side in self.sides:
            all_vertices.extend(side.get_vertices())
        
        if not all_vertices:
            return None
        
        center = Vertex(0, 0, 0)
        for v in all_vertices:
            center = center + v
        return center.scale(1.0 / len(all_vertices))

    def get_bounding_box(self):
        """Get the bounding box of this solid"""
        all_vertices = []
        for side in self.sides:
            all_vertices.extend(side.get_vertices())
        
        if not all_vertices:
            return None, None
        
        # initialize with first vertex 
        first_v = all_vertices[0]
        min_v = Vertex(first_v.x, first_v.y, first_v.z)
        max_v = Vertex(first_v.x, first_v.y, first_v.z)
        
        for v in all_vertices[1:]:
            min_v.x = min(min_v.x, v.x)
            min_v.y = min(min_v.y, v.y)
            min_v.z = min(min_v.z, v.z)
            max_v.x = max(max_v.x, v.x)
            max_v.y = max(max_v.y, v.y)
            max_v.z = max(max_v.z, v.z)
        
        return min_v, max_v

class VMFParser:
    def __init__(self):
        self.entities = []
        self.world = {}
        self.versioninfo = {}
        self.viewsettings = {}
        self.cameras = {}
        self.cordons = {}
        self.solids = []

    def parse(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise IOError(f"Error reading file: {e}")
        
        tokens = self.tokenize(content)
        if not tokens:
            raise ValueError("No tokens found in file")
            
        self.data = self.parse_block(iter(tokens))
        self.extract_data(self.data)

    def tokenize(self, content):
        # tokenization with better quote handling
        token_pattern = r'"[^"]*"|[^\s{}"]+|[{}]'
        tokens = re.findall(token_pattern, content)
        return [token.strip() for token in tokens if token.strip()]

    def parse_block(self, tokens):
        data = {}
        key = None
        
        while True:
            try:
                token = next(tokens)
            except StopIteration:
                break
            
            if token == '}':
                return data
            elif token == '{':
                if key is None:
                    logging.warning("Unexpected '{' without key")
                    continue
                    
                value = self.parse_block(tokens)
                if key in data:
                    if not isinstance(data[key], list):
                        data[key] = [data[key]]
                    data[key].append(value)
                else:
                    data[key] = value
                key = None
            elif token.startswith('"'):
                if key is None:
                    key = token.strip('"')
                else:
                    value = token.strip('"')
                    if key in data:
                        if not isinstance(data[key], list):
                            data[key] = [data[key]]
                        data[key].append(value)
                    else:
                        data[key] = value
                    key = None
            else:
                if key is None:
                    key = token
                else:
                    # handle unquoted values
                    if key in data:
                        if not isinstance(data[key], list):
                            data[key] = [data[key]]
                        data[key].append(token)
                    else:
                        data[key] = token
                    key = None
        
        return data

    def extract_data(self, data):
        if not isinstance(data, dict):
            logging.warning("Invalid VMF data structure")
            return
            
        self.versioninfo = data.get('versioninfo', {})
        self.viewsettings = data.get('viewsettings', {})
        self.world = data.get('world', {})
        self.cameras = data.get('cameras', {})
        self.cordons = data.get('cordons', {})
        
        # parse world solids
        if self.world:
            world_solids = self.world.get('solid', [])
            if not isinstance(world_solids, list):
                world_solids = [world_solids] if world_solids else []
            
            for solid_data in world_solids:
                if solid_data:
                    solid = Solid()
                    solid.parse(solid_data)
                    self.solids.append(solid)
        
        # parse entities and their solids
        entities_data = data.get('entity', [])
        if not isinstance(entities_data, list):
            entities_data = [entities_data] if entities_data else []
        
        for entity_data in entities_data:
            if entity_data:
                self.entities.append(entity_data)
                entity_solids = entity_data.get('solid', [])
                if entity_solids:
                    if not isinstance(entity_solids, list):
                        entity_solids = [entity_solids]
                    for solid_data in entity_solids:
                        if solid_data:
                            solid = Solid()
                            solid.parse(solid_data)
                            self.solids.append(solid)

def get_all_materials(solids):
    """Extract all unique materials from the map"""
    materials = set()
    for solid in solids:
        for side in solid.sides:
            if side.material:
                materials.add(side.material)
    return sorted(list(materials))

def create_trigger_brush_simple(base_vertices, normal, height=4):
    """Create a simple box trigger that extends from the surface"""
    if len(base_vertices) < 3:
        return None
    
    # create top vertices by extending in normal direction
    top_vertices = [v + normal.scale(height) for v in base_vertices]
    
    # build the brush faces
    faces = []
    
    # bottom face (the original surface) - vertices in reverse order
    faces.append(list(reversed(base_vertices)))
    
    # top face - vertices in forward order
    faces.append(top_vertices)
    
    # side faces - connect bottom to top
    num_verts = len(base_vertices)
    for i in range(num_verts):
        next_i = (i + 1) % num_verts
        side_face = [
            base_vertices[i],
            base_vertices[next_i],
            top_vertices[next_i],
            top_vertices[i]
        ]
        faces.append(side_face)
    
    return faces

def create_trigger_entity(solid_id, face_id_start, base_side, height=4):
    """Create a trigger_multiple entity from a surface"""
    base_vertices = base_side.get_vertices()
    if not base_vertices or len(base_vertices) < 3:
        return None, face_id_start
    
    normal = base_side.compute_normal()
    if normal is None:
        return None, face_id_start
    
    # create the brush faces
    brush_faces = create_trigger_brush_simple(base_vertices, normal, height)
    if not brush_faces:
        return None, face_id_start
    
    # build vmf structure
    vmf_sides = []
    face_id = face_id_start
    
    for face_vertices in brush_faces:
        if len(face_vertices) < 3:
            continue
        
        plane_points = face_vertices[:3]
        plane_str = ' '.join([f"({v.x:.6f} {v.y:.6f} {v.z:.6f})" for v in plane_points])
        
        vertices_plus = {'v': [f"{v.x:.6f} {v.y:.6f} {v.z:.6f}" for v in face_vertices]}
        
        side_data = {
            'id': str(face_id),
            'plane': plane_str,
            'vertices_plus': vertices_plus,
            'material': 'TOOLS/TOOLSTRIGGER',
            'uaxis': '[1 0 0 0] 0.25',
            'vaxis': '[0 -1 0 0] 0.25',
            'rotation': '0',
            'lightmapscale': '16',
            'smoothing_groups': '0'
        }
        
        vmf_sides.append(side_data)
        face_id += 1
    
    # create the solid
    trigger_solid = {
        'id': str(solid_id),
        'side': vmf_sides,
        'editor': {
            'color': '220 30 220',
            'visgroupshown': '1',
            'visgroupautoshown': '1'
        }
    }
    
    # create the entity
    trigger_entity = {
        'id': str(solid_id + 1),
        'classname': 'trigger_multiple',
        'spawnflags': '1',
        'StartDisabled': '0',
        'wait': '0',
        'solid': trigger_solid,
        'editor': {
            'color': '220 30 220',
            'visgroupshown': '1',
            'visgroupautoshown': '1'
        }
    }
    
    return trigger_entity, face_id

def write_vmf_block(f, name, content, indent=0):
    """Write a VMF block to file"""
    ind = '\t' * indent
    f.write(f'{ind}{name}\n{ind}{{\n')
    
    for key, value in content.items():
        if isinstance(value, dict):
            write_vmf_block(f, key, value, indent + 1)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    write_vmf_block(f, key, item, indent + 1)
                else:
                    f.write(f'{ind}\t"{key}" "{item}"\n')
        else:
            f.write(f'{ind}\t"{key}" "{value}"\n')
    
    f.write(f'{ind}}}\n')

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("TRIGGER GENERATOR FOR HAMMER++")
    print("="*60)
    print("\nThis script generates trigger_multiple entities for")
    print("surfaces with specified materials.")
    print("-"*60 + "\n")
    
    # get input file
    if len(sys.argv) < 2:
        input_file = input("Enter VMF file path: ").strip()
        if not input_file:
            logging.error("No file specified. Exiting.")
            sleep(3)
            return
    else:
        input_file = sys.argv[1]
    
    logging.info(f"Loading map: {input_file}")
    
    # parse vmf
    try:
        parser = VMFParser()
        parser.parse(input_file)
        logging.info(f"Successfully parsed VMF with {len(parser.solids)} solids")
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sleep(3)
        return
    except Exception as e:
        logging.error(f"Failed to parse VMF: {e}")
        logging.debug(traceback.format_exc())
        sleep(3)
        return
    
    # get all materials
    all_materials = get_all_materials(parser.solids)
    
    print("\n" + "-"*60)
    print(f"Found {len(all_materials)} unique materials")
    print("-"*60)
    
    if all_materials:
        print("\nMaterials in your map:")
        for i, mat in enumerate(all_materials, 1):
            print(f"  {i}. {mat}")
        print()
    else:
        logging.warning("No materials found in the map")
    
    # get materials to trigger
    print("Enter materials to trigger (comma-separated)")
    print("Examples: 'dev/dev_measuregeneric01' or just 'dev' for all dev textures")
    materials_input = input("Materials: ").strip()
    
    if not materials_input:
        logging.error("No materials specified. Exiting.")
        sleep(3)
        return
    
    target_materials = [mat.strip().lower() for mat in materials_input.split(',')]
    logging.info(f"Target materials: {target_materials}")
    
    # get trigger height
    height_input = input("\nTrigger height in units (default 4): ").strip()
    trigger_height = 4
    if height_input:
        try:
            trigger_height = float(height_input)
            if trigger_height <= 0:
                logging.warning("Height must be positive. Using default: 4 units")
                trigger_height = 4
        except ValueError:
            logging.warning("Invalid input. Using default: 4 units")
    logging.info(f"Using trigger height: {trigger_height} units")
    
    # ask if user wants debug output
    debug_input = input("\nShow detailed surface analysis? (y/n, default n): ").strip().lower()
    show_debug = debug_input == 'y'
    
    # find max ids more efficiently
    max_solid_id = 10000
    max_face_id = 20000
    
    for solid in parser.solids:
        # fixed: check if id exists and is not none before calling isdigit()
        if solid.id and isinstance(solid.id, str) and solid.id.isdigit():
            max_solid_id = max(max_solid_id, int(solid.id))
        for side in solid.sides:
            if side.id and isinstance(side.id, str) and side.id.isdigit():
                max_face_id = max(max_face_id, int(side.id))
    
    solid_id_counter = max_solid_id + 1
    face_id_counter = max_face_id + 1
    
    logging.info(f"Starting IDs - solid: {solid_id_counter}, face: {face_id_counter}")
    
    # process surfaces
    new_triggers = []
    triggered_materials = set()
    surface_stats = {
        "total_matching": 0,
        "walls_skipped": 0,
        "non_planar_skipped": 0,
        "floor": 0,
        "ceiling": 0,
        "ramp": 0,
        "steep_slope": 0,
        "ceiling_ramp": 0,
        "steep_ceiling_slope": 0,
        "gentle_slope": 0,
        "gentle_ceiling_slope": 0
    }
    
    # track angle distribution
    angle_distribution = []
    
    print("\nProcessing surfaces...")
    
    for solid_idx, solid in enumerate(parser.solids):
        for side_idx, side in enumerate(solid.sides):
            if not side.material:
                continue
            
            # check if material matches
            material_lower = side.material.lower()
            matches = False
            for target in target_materials:
                if target in material_lower:
                    matches = True
                    break
            
            if not matches:
                continue
            
            surface_stats["total_matching"] += 1
            
            # check if planar
            if not side.is_planar(tolerance=1.0):
                surface_stats["non_planar_skipped"] += 1
                if show_debug:
                    print(f"  Skipping non-planar surface: {side.material}")
                continue
            
            # check if surfable
            if not side.is_surfable():
                surface_stats["walls_skipped"] += 1
                continue
            
            # get detailed surface info
            normal = side.compute_normal()
            if not normal:
                continue
                
            surface_type = side.get_surface_type()
            angle = side.get_angle_from_horizontal()
            
            if surface_type in surface_stats:
                surface_stats[surface_type] += 1
            
            if angle is not None:
                angle_distribution.append(angle)
            
            # debug output
            if show_debug:
                print(f"\n  Solid {solid_idx}, Side {side_idx}:")
                print(f"    Material: {side.material}")
                print(f"    Normal: ({normal.x:.3f}, {normal.y:.3f}, {normal.z:.3f})")
                print(f"    Angle from horizontal: {angle:.1f}°" if angle else "    Angle: unknown")
                print(f"    Type: {surface_type}")
                print(f"    Vertices: {len(side.get_vertices())}")
                
                # show bounding box for context
                try:
                    min_v, max_v = solid.get_bounding_box()
                    if min_v and max_v:
                        size_x = max_v.x - min_v.x
                        size_y = max_v.y - min_v.y
                        size_z = max_v.z - min_v.z
                        print(f"    Solid size: {size_x:.0f} x {size_y:.0f} x {size_z:.0f}")
                except Exception as e:
                    print(f"    Could not calculate bounding box: {e}")
            
            # create trigger
            try:
                trigger_entity, face_id_counter = create_trigger_entity(
                    solid_id_counter, face_id_counter, side, trigger_height
                )
                
                if trigger_entity:
                    new_triggers.append(trigger_entity)
                    triggered_materials.add(side.material)
                    solid_id_counter += 2
                
            except Exception as e:
                logging.warning(f"Failed to create trigger for side {side.id}: {e}")
    
    # analyze angle distribution
    if angle_distribution and show_debug:
        print("\n" + "-"*60)
        print("ANGLE DISTRIBUTION (from horizontal):")
        print(f"  Min: {min(angle_distribution):.1f}°")
        print(f"  Max: {max(angle_distribution):.1f}°")
        print(f"  Average: {sum(angle_distribution)/len(angle_distribution):.1f}°")
        
        # histogram
        ranges = [
            (0, 10, "Nearly flat"),
            (10, 30, "Gentle slope"),
            (30, 45, "Moderate slope"),
            (45, 60, "Steep slope"),
            (60, 80, "Very steep"),
            (80, 90, "Nearly vertical")
        ]
        
        print("\nDistribution by angle:")
        for min_angle, max_angle, label in ranges:
            count = sum(1 for a in angle_distribution if min_angle <= a < max_angle)
            if count > 0:
                print(f"  {label} ({min_angle}°-{max_angle}°): {count} surfaces")
    
    # report results
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"\nSurfaces with matching materials: {surface_stats['total_matching']}")
    print(f"  Walls skipped: {surface_stats['walls_skipped']}")
    print(f"  Non-planar skipped: {surface_stats['non_planar_skipped']}")
    print(f"\nSurfaces triggered by type:")
    print(f"  Floors: {surface_stats['floor']}")
    print(f"  Ceilings: {surface_stats['ceiling']}")
    print(f"  Gentle slopes: {surface_stats['gentle_slope']}")
    print(f"  Ramps/slopes: {surface_stats['ramp']}")
    print(f"  Steep slopes: {surface_stats['steep_slope']}")
    print(f"  Ceiling ramps: {surface_stats['ceiling_ramp']}")
    print(f"  Steep ceiling slopes: {surface_stats['steep_ceiling_slope']}")
    print(f"  Gentle ceiling slopes: {surface_stats['gentle_ceiling_slope']}")
    print(f"\nTotal triggers created: {len(new_triggers)}")
    
    if triggered_materials:
        print("\nMaterials triggered:")
        for mat in sorted(triggered_materials):
            print(f"  - {mat}")
    
    if len(new_triggers) == 0:
        print("\n" + "!"*60)
        print("WARNING: No triggers were generated!")
        print("Check your material names and try enabling debug mode.")
        print("!"*60)
        sleep(5)
        return
    
    # write output
    output_file = "generated_triggers.vmf"
    print(f"\nWriting {len(new_triggers)} triggers to: {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # write header sections, need to do more here
            if parser.versioninfo:
                write_vmf_block(f, 'versioninfo', parser.versioninfo)
            if parser.viewsettings:
                write_vmf_block(f, 'viewsettings', parser.viewsettings)
            
            # write world
            f.write('world\n{\n')
            for key, value in parser.world.items():
                if key == 'solid':
                    continue
                if isinstance(value, (dict, list)):
                    continue
                f.write(f'\t"{key}" "{value}"\n')
            
            # write world solids
            world_solids = parser.world.get('solid', [])
            if not isinstance(world_solids, list):
                world_solids = [world_solids] if world_solids else []
            for solid_data in world_solids:
                if solid_data:
                    write_vmf_block(f, 'solid', solid_data, 1)
            f.write('}\n')
            
            # write existing entities
            for entity_data in parser.entities:
                if entity_data:
                    write_vmf_block(f, 'entity', entity_data)
            
            # write new triggers
            for trigger in new_triggers:
                write_vmf_block(f, 'entity', trigger)
            
            # write footer sections
            if parser.cameras:
                write_vmf_block(f, 'cameras', parser.cameras)
            if parser.cordons:
                write_vmf_block(f, 'cordons', parser.cordons)
        
        print("\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        print(f"\nGenerated {len(new_triggers)} trigger_multiple entities")
        print(f"Output saved to: {output_file}")
        print("\nYou can now import this VMF into Hammer++")
        print("="*60 + "\n")
        
    except Exception as e:
        logging.error(f"Failed to write output file: {e}")
        logging.debug(traceback.format_exc())
        sleep(3)
        return
    
    input("\nPress Enter to exit...")

if __name__ == '__main__':
    main()
