"""
macOS virtual audio setup helper using BlackHole.

BlackHole acts as both a capture device (recording meeting audio)
and a playback device (injecting TTS audio as virtual mic input).

Setup instructions (one-time):
  1. brew install blackhole-2ch
  2. Open "Audio MIDI Setup" → create Multi-Output Device:
       - Check "BlackHole 2ch" + "Built-in Output"
  3. System Preferences → Sound → Output → select "Multi-Output Device"
  4. In Teams: Settings → Devices → Microphone → "BlackHole 2ch"

After setup, system audio (including Teams meeting) flows into BlackHole,
which Python can read. TTS audio written to BlackHole is picked up by Teams
as microphone input.
"""

import sounddevice as sd


def list_devices() -> list[dict]:
    """Return all available audio devices."""
    devices = sd.query_devices()
    return [
        {"index": i, "name": d["name"], "inputs": d["max_input_channels"], "outputs": d["max_output_channels"]}
        for i, d in enumerate(devices)
    ]


def find_device_index(name: str, kind: str = "input") -> int:
    """
    Find device index by name substring.

    Args:
        name: Substring to match against device name (e.g. "BlackHole 2ch")
        kind: "input" or "output"

    Returns:
        Device index or raises RuntimeError if not found.
    """
    devices = sd.query_devices()
    channel_key = "max_input_channels" if kind == "input" else "max_output_channels"
    for i, d in enumerate(devices):
        if name.lower() in d["name"].lower() and d[channel_key] > 0:
            return i
    raise RuntimeError(
        f"Audio device '{name}' ({kind}) not found.\n"
        "Please install BlackHole: brew install blackhole-2ch\n"
        f"Available devices: {[d['name'] for d in devices]}"
    )


def get_capture_device_index(device_name: str) -> int:
    """Return input device index for audio capture (recording meeting audio)."""
    return find_device_index(device_name, kind="input")


def get_playback_device_index(device_name: str) -> int:
    """Return output device index for TTS playback (virtual mic injection)."""
    return find_device_index(device_name, kind="output")


def print_setup_guide() -> None:
    print(
        "\n=== BlackHole Setup Guide ===\n"
        "1. Install: brew install blackhole-2ch\n"
        "2. Open 'Audio MIDI Setup' (Spotlight search)\n"
        "   → Click '+' → 'Create Multi-Output Device'\n"
        "   → Check 'BlackHole 2ch' and 'Built-in Output'\n"
        "3. System Preferences → Sound → Output → 'Multi-Output Device'\n"
        "4. In Microsoft Teams:\n"
        "   Settings → Devices → Microphone → 'BlackHole 2ch'\n"
        "5. Set CAPTURE_DEVICE=BlackHole 2ch in environment\n"
        "================================\n"
    )
