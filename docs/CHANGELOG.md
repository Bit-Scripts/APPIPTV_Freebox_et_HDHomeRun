# Changelog

## [1.5.0] - 2026-10-20
### Added
- Native libmpv/OpenGL playback inside PyQt6 on Wayland.
- Current Freebox logo catalogue with background refresh and local fallback.
- Local Conda launcher for the desktop shortcut.

### Changed
- Keep a 16:9 TV frame with channel and current-program overlays.
- Migrate dependencies, documentation and packaging configuration to mpv.

### Fixed
- Restore the C numeric locale after Qt initialization to prevent startup crashes.
- Wrap long errors without forcing window or channel-list dimensions.
- Reconnect selected stream URLs, pause, volume, error recovery and player cleanup.

## [1.3.0] - 2024-05-19
### Added
- New bluish dark theme.
- Improved dynamic library management for Windows.

### Fixed
- Historical (former VLC backend): bug with loading `libvlc.dll` on Windows.

## [1.2.0] - 2024-04-15
### Added
- Support for HDHomeRun devices.
- Enhanced user interface with PyQt6.
