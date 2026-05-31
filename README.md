# Closest Plane — Home Assistant Integration

A Home Assistant custom component that finds the nearest airborne aircraft to your location and exposes it as a set of sensors. Self-contained Python — does not require the Node.js closest-plane-app to be running.

## What it does

Every N minutes (configurable), the integration:

1. Queries OpenSky Network for aircraft within your configured radius
2. Picks the closest airborne aircraft
3. Enriches it via ADSBDB (aircraft identity, typical route), AeroDataBox and/or AviationStack (live departure/destination and times)
4. Exposes the result as Home Assistant sensor entities

## Sensors

| Entity | Example value | Notes |
|---|---|---|
| `sensor.closest_plane_callsign` | `EXS18QH` | Raw transponder callsign; also carries full route data as attributes |
| `sensor.closest_plane_flight_number` | `LS 1728` | Normalised IATA flight number |
| `sensor.closest_plane_airline` | `Jet2.com` | |
| `sensor.closest_plane_airline_logo_url` | `https://images.kiwi.com/…` | Airline logo URL for use in dashboard cards |
| `sensor.closest_plane_departure` | `AYT - Antalya Airport` | |
| `sensor.closest_plane_destination` | `MAN - Manchester Airport` | |
| `sensor.closest_plane_departure_time` | `2024-05-31T09:30:00+00:00` | Actual departure if known, otherwise scheduled |
| `sensor.closest_plane_arrival_time` | `2024-05-31T12:15:00+00:00` | Estimated arrival if known, otherwise scheduled |
| `sensor.closest_plane_scheduled_departure` | `2024-05-31T09:15:00+00:00` | |
| `sensor.closest_plane_actual_departure` | `2024-05-31T09:30:00+00:00` | |
| `sensor.closest_plane_scheduled_arrival` | `2024-05-31T12:00:00+00:00` | |
| `sensor.closest_plane_estimated_arrival` | `2024-05-31T12:15:00+00:00` | |
| `sensor.closest_plane_registration` | `G-SUNU` | |
| `sensor.closest_plane_aircraft_type` | `A21N` | ICAO type code |
| `sensor.closest_plane_aircraft_model` | `Airbus A321-251NX` | |
| `sensor.closest_plane_distance_km` | `16.15` | km |
| `sensor.closest_plane_altitude_ft` | `37225` | ft |
| `sensor.closest_plane_speed_knots` | `435` | kn |
| `sensor.closest_plane_heading` | `304` | degrees |
| `sensor.closest_plane_vertical_rate_fpm` | `0` | ft/min |
| `sensor.closest_plane_remaining_minutes` | `92` | minutes to destination |
| `sensor.closest_plane_elapsed_minutes` | `169` | minutes since departure |
| `sensor.closest_plane_icao24` | `40825f` | Mode S transponder hex |
| `sensor.closest_plane_origin_country` | `United Kingdom` | |
| `sensor.closest_plane_squawk` | `3120` | |

The `callsign` sensor carries extended attributes: departure/destination airport objects, scheduled/actual/estimated times, total flight minutes, position, confidence scores, and enrichment sources.

## Dashboard card

Add a **Markdown card** to your dashboard with the following content:

```yaml
type: markdown
content: >
  {% set logo = states('sensor.closest_plane_airline_logo_url') %}
  {% if logo not in ('unknown', 'unavailable', '') %}
  <img src="{{ logo }}" height="40"/>
  {% endif %}

  {{ states('sensor.closest_plane_airline') }} | {{ states('sensor.closest_plane_aircraft_model') }}

  ✈ {{ states('sensor.closest_plane_departure') }} → {{ states('sensor.closest_plane_destination') }}

  Alt: {{ states('sensor.closest_plane_altitude_ft') }} ft | Spd: {{ states('sensor.closest_plane_speed_knots') }} kn | Hdg: {{ states('sensor.closest_plane_heading') }}° | Vert: {{ states('sensor.closest_plane_vertical_rate_fpm') }} ft/min
```

## Installation

### HACS (recommended)

1. Open HACS → Integrations → three-dot menu → Custom repositories
2. Add `https://github.com/bairnhard/closest-plane-ha` as category **Integration**
3. Install **Closest Plane**, restart Home Assistant

### Manual

```bash
cp -r custom_components/closest_plane /config/custom_components/
```

Restart Home Assistant, then add the integration via **Settings → Devices & Services → Add Integration → Closest Plane**.

## Configuration

**Step 1 — Location & radius**

| Field | Default | Description |
|---|---|---|
| Latitude | HA home | Centre of search area |
| Longitude | HA home | Centre of search area |
| Search radius | 180 km | Max 500 km |
| Refresh interval | 2 min | Min 1 min |

**Step 2 — API keys (all optional)**

| Field | Description |
|---|---|
| OpenSky client ID / secret | OAuth credentials for higher rate limits. Create at [opensky-network.org](https://opensky-network.org/). Without these, anonymous access is used (more restrictive). |
| AviationStack API key | Live departure/arrival times by flight number. Free tier: 1000 calls/month. Get at [aviationstack.com](https://aviationstack.com/). Results are cached for 3 hours per flight number to stay well within the free quota. |
| AeroDataBox RapidAPI key | Live route data by ICAO24 transponder code (~5 min lag). Paid. Get at [rapidapi.com](https://rapidapi.com/) → search AeroDataBox. Takes priority over AviationStack when both are configured. |
| Manual cache directory | Absolute path to a `.cache` directory in the same format as [closest-plane-app](https://github.com/bairnhard/closest-plane-app). Allows sharing manual flight and aircraft overrides between the two tools. |

## Data sources and priority

Route data (departure/arrival times and airports):

1. **AeroDataBox** — live data by ICAO24, ~5 min lag (paid)
2. **AviationStack** — live data by flight number, only called when AeroDataBox yields no times (free: 1000/month, cached 3h per flight)
3. **ADSBDB** — typical/historical route for known callsigns (airports only, no times)
4. **Local flight cache** (`flight-cache.json`) — user-verified ground truth, applied on top
5. **OpenSky flights** — last resort, historical ICAO airport codes only, no times

Aircraft identity:

1. **Local aircraft cache** (`aircraft-cache.json`)
2. **ADSBDB** — registration, type, model, operator
3. **AeroDataBox** — registration fallback

## Honest data boundary

OpenSky live state vectors do not contain departure/destination. Route and timing fields are only populated from ADSBDB, AviationStack, AeroDataBox, or manual caches. When unknown, the relevant sensors are unavailable rather than showing guessed data. Rescue helicopters and general aviation typically have no route data.

## Automation example

```yaml
automation:
  - alias: "Interesting aircraft overhead"
    trigger:
      - platform: numeric_state
        entity_id: sensor.closest_plane_distance_km
        below: 20
        above: 0
    condition:
      - condition: not
        conditions:
          - condition: state
            entity_id: sensor.closest_plane_airline
            state: unavailable
    action:
      - service: notify.mobile_app
        data:
          title: "Aircraft overhead"
          message: >
            {{ states('sensor.closest_plane_flight_number') }}
            ({{ states('sensor.closest_plane_airline') }})
            {{ states('sensor.closest_plane_distance_km') }} km away at
            {{ states('sensor.closest_plane_altitude_ft') }} ft.
            {% if states('sensor.closest_plane_departure') != 'unavailable' %}
            {{ states('sensor.closest_plane_departure') }} →
            {{ states('sensor.closest_plane_destination') }}
            {% endif %}
```

## Development

CI runs three checks on every push and pull request (see `.github/workflows/validate.yml`):

| Check | Tool | What it catches |
|---|---|---|
| Lint & security | `ruff check` | Style, bugs, complexity, and security issues (covers bandit ruleset) |
| Formatting | `ruff format --check` | Consistent code style |
| HA validation | `hassfest` | Manifest, translations, and integration structure |
| HACS validation | `hacs/action` | HACS compatibility |

Run checks locally before pushing:

```bash
pip install ruff
ruff check custom_components/        # lint + security
ruff format custom_components/       # auto-format
```

### HACS publishing checklist

Two steps must be done manually in GitHub before HACS validation fully passes:

1. **Add repository topics** — go to the repository page → gear icon next to "About" → add topics:
   `home-assistant`, `hacs`, `homeassistant-integration`

2. **Add brand icon** — place a 256×256 PNG at `custom_components/closest_plane/brand/icon.png`.
   Optionally add `icon@2x.png` (512×512) for HiDPI. Any icon editor or
   [realfavicongenerator.net](https://realfavicongenerator.net) can produce the right size.

## Relation to closest-plane-app

This integration is a self-contained Python reimplementation of the data pipeline from [closest-plane-app](https://github.com/bairnhard/closest-plane-app). The two share the same JSON cache file format — if you run both on the same machine, point `cache_dir` at the Node.js app's `.cache` directory to share manual enrichment entries.
