## hammer++ automatic trigger generator

a python script that automatically generates trigger_multiple entities for surfable or walkable surfaces in counter-strike: source maps. work in progress. uses hammer++ precise vertices, untested but probably won't work in regular hammer. making this to help create tricksurf maps.

heavily beta and will not work across all maps or untested platforms, right now it is for simple trigger generation. you'll probably get errors for more complex maps

## features

- **automatic smart surface detection**: identifies floors, ceilings, ramps, and slopes based on surface normals
- **hammer++ enhanced**: uses hammer++ `vertices_plus` keyvalues for precision
- **non-destructive**: preserves all existing map geometry and entities and creates a new vmf file

## output

the script generates a new file called `generated_triggers.vmf` containing:
- original map geometry
- new trigger_multiple entities for each detected surface
- preserved entity IDs to avoid conflicts

## usage

1. **run from command line**: `py autotrigger.py map.vmf` with script and map in the same directory
2. **material selection**: choose which materials to create triggers for
   - example: `dev` for all dev textures
   - example: `dev/dev_measuregeneric01` for specific texture
   - multiple materials: `dev,tools/toolsnodraw,concrete/concretefloor` (comma-separated)
3. **trigger height**: how far out from the surface should the trigger extend (default: 4 units)
4. **debug mode / detailed analysis (y/n)**: spews detailed surface analysis for every solid parsed
   - individual surface normals
   - angle measurements
   - surface classifications
   - solid bounding boxes
   - angle distribution histogram

## requirements

- python 3.6 up
- VMF file saved in hammer++ (only tested with counter-strike: source)
- no external dependencies

## surface classification

| surface type | normal z-component | angle from horizontal |
|-------------|-------------------|----------------------|
| wall | < 0.01 | ~90° |
| floor | ≥ 0.985 | < 10° |
| steep slope | 0.7 - 0.985 | 10° - 45° |
| ramp/slope | 0.3 - 0.7 | 45° - 73° |
| gentle slope | 0.01 - 0.3 | 73° - 89° |

## trigger generation

for each qualifying surface:
1. calculates the outward-facing normal
2. creates a trigger brush extending from the surface
3. assigns trigger_multiple properties

