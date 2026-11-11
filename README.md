# MySims Hashlists

Hashlists are named after the full game name (for example, `mysims-cozy-bundle.hashlist` for MySims Cozy Bundle). Each line contains a hashed filename followed by its unhashed name. Example: `0x00000000!0xda00dd498ceaa11a.0xf3593628 Fountain_AudioDef.xml`, a space inbetween with a newline at the end.

- **Unpruned** (`.hashlist`) includes candidate names, even when the corresponding files are not present in the game.
- **Pruned** (`.hashlist.pruned`) contains only entries whose hashed or unhashed filename was found in the scanned game data folder.

## Tools

The scripts require Python 3. Run them from the repository root:

```sh
python tools/prune.py <hashlist> <game_folder> <file_types>
python tools/check.py <hashlist> <game_folder> <file_types>
```

`game_folder` is the game data folder. `file_types` is a file-association list such as `DDFMap.txt`, with one type ID and extension per line (for example, `0x00b2d882 dds`). Quote paths that contain spaces.

`prune.py` scans the folder recursively and writes `<hashlist>.pruned`. `check.py` counts hashed files in the folder that cannot be matched using the hashlist.
