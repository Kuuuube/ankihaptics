# Anki Haptics

Haptics device integration for Anki.

## Setup

1. Install [Intiface Central](https://intiface.com/central/)

2. Run Intiface Central and start the server by clicking on the top left start button (▶). (Optionally, enable `Start Server when Intiface Central Launches` in `App Modes`)

3. Start Anki. If Anki was already started, go to `Tools > Anki Haptics Settings` and click `Reconnect`.

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

## Development

Run `setup.sh` to generate the `lib` folder with dependencies.

Run `release.sh` to generate a zipped release build.
