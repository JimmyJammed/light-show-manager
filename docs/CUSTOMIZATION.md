# Customization

Edit Show duration and timestamps; pass your device operations as functions. Give every blocking device request a timeout. Configure worker count for the device/network capacity. Use named descriptions to identify failing cues.

Save device state in pre_show and restore it in post_show. Pass shared handles through context. Hooks must tolerate partial setup. Cleanup completes before replacement playback begins. Python cannot forcibly terminate a worker thread; a hung blocking function also blocks safe restoration.

For deterministic simulations inject a clock function and matching async sleep function. For audio, implement AudioBackend or use SilentBackend. Core code never needs to depend on a particular lighting vendor.
