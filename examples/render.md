# Render configuration

Rendering settings are specified in the configuration files and many
of them have defaults that are used if the value is not specified (or
the file is not provided).

## Default settings

Height of the sun as the polar angle limits, colour of the emission
(RGBA value), size of the sun (shadow), and sun strength which will
determine the overall lighting as well as the balance with the sky
colour together with the film exposure:

```json
"sun_theta": [
    0,
    1.48352986419518
],
"sun_color": [
    1.0,
    1.0,
    0.984313725490196,
    1.0
],
"sun_size": 0.02,
"sun_strength": 4,
```

Camera clearance above ground, relative distance from the sphere, and
a list of objects to exclude if calculating bounding spheres (if none
are specified), the first object of which will also be used to choose
the height (only when using bounding spheres to position the camera):

```json
"camera_clearance": [
    3,
    4.6
],
"camera_distance_factor": {
    "mean": 0.8,
    "sigma": 0.1
},
"landscape": [
    "Landscape"
],
```

Sigma of the polar angle around horizontal and noise for camera
location (only when using lines for camera placement):

```json
"camera_sigma": 0.26,
"camera_location_noise": 0.1,
```

Noise for the camera rotation, parameters for the lognormal camera
lens focal length distribution, and the furthest distance objects are
visible to the camera:

```json
"camera_noise": 0.01,
"camera_lens": {
    "log_sigma": 0.25,
    "mean": 16
},
"camera_clip_end": 100000,
```

Resolution of images to render, relative exposure that determines the
overall brightness (see notes above on sun strength), number of
samples to use when rendering (higher number for less noise), maximum
brightness value for reflected rays (setting below 1.0 reduces
speckles but increases noise), and mist intensity:

```json
"resolution": [
    512,
    512
],
"film_exposure": 2,
"cycles_samples": 64,
"clamp_indirect": 0.8,
"compositing_mist": 0.04,
```

## General settings

Cloud parameters (when the *World* material is appropriately set up)
are the size of the clouds as the noise scale lognormal distribution
parameters, a random translation limits of the noise, and limits on
the relative amount of the sky that clouds cover with a parameter to
set the sharpness of the edges:

```json
"sky": {
    "noise_scale": {
        "log_sigma": 0.25,
        "mean": 4.0
    },
    "translate": [
        0.0,
        4.0
    ],
    "cloud_ramp": {
        "max": 0.8,
        "diff": 0.2,
        "min": 0.2
    }
},
```

Manually defined bounding spheres named descriptively:

```json
"spheres": {
    "my-carefully-placed-sphere": {
        "centre": [
            -37,
            -45,
            155
        ],
        "radius": 10
    },
    ...
},
```

Place the camera on lines with given end points:

```json
"lines": {
    "diagonal-line-over-bridge": {
        "end": [
            -59,
            -67,
            158
        ],
        "start": [
            11,
            15,
            159
        ]
    },
    ...
}
```
