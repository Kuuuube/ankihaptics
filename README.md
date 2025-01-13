# Anki Haptics

Haptics device integration for Anki.

## Setup

1. Install [Intiface Central](https://intiface.com/central/)

2. Run Intiface Central and start the server by clicking on the top left start button (▶). (Optionally, enable `Start Server when Intiface Central Launches` in `App Modes`)

3. Install the Anki Haptics addon.

    - Open Anki.

    - On the top menu, go to `Tools` > `Add-ons`.

    - Click `Get Add-ons...`.

    - Input `247550864`

    - Click `OK`.

    - Restart Anki

4. Start Anki. If Anki was already started, go to `Tools` > `Anki Haptics Settings` and click `Reconnect`.

5. In `Tools` > `Anki Haptics Settings`, enable your device and configure your settings.

## Usage

Haptics activation are supported for the following Anki actions:

```
Again button press
Hard button press
Good button press
Easy button press
Show question
Show answer
```

All actions can be configured individually in settings.

## Troubleshooting

### Scanning can't find device

Sometimes, requesting to scan for a device through Anki Haptics doesn't work.

Connect your device through scanning in Intiface directly instead and Anki Haptics will find it without needing to scan.

(You may need to restart Intiface if it has already failed once through Anki Haptics)

## Info

[Github Repository](https://github.com/Kuuuube/ankihaptics)

[Report Issues Here](https://github.com/Kuuuube/ankihaptics/issues)
