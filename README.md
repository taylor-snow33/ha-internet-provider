# RV Internet Provider

A custom Home Assistant integration for the free HTTPS IPWhois endpoint. It identifies the public internet connection **Home Assistant itself uses**, including a UniFi failover connection, without a UniFi login or API key.

Version 0.1.0. Targets Home Assistant 2026.10 or later. This is a third-party custom integration, not a Home Assistant core integration or an official IPWhois product.

## What you get

One device, **RV Internet Provider**, with 27 sensors and 3 binary sensors:

- ISP, network organization, ASN, network domain, public IP and IP version.
- IP-based continent/country/region/city, codes, latitude, longitude, postal code, calling code, capital and bordering country codes.
- Flag URL, emoji and Unicode representation.
- IP time-zone identifier, abbreviation, UTC offsets and provider timestamp.
- Lookup successful, IP country in EU and IP daylight saving time.

The **Public IP** sensor's `response` attribute also exposes the complete successful JSON response, including any extra fields the provider returns. Its `last_successful_lookup` attribute timestamps the fetch. Optional fields missing from the response are unavailable, not fabricated. Currency, security/VPN detection, and native-language fields require paid service plans and are **not promised by this free endpoint**. The integration does not request or support a paid endpoint.

All entities share **one request every 300 seconds** by default, not one request per sensor. The Options UI allows 300–3600 seconds. The documented free quota is 1,000 requests/day per public IP; 5-minute polling uses 288/day, plus setup/reload requests. Other users behind carrier-grade NAT can share your quota. HTTP 429 respects `Retry-After` (24-hour fallback). Quota cooldown is retained through entry reloads, but not HA restarts. There is no service uptime guarantee.

## Install manually

1. Back up Home Assistant.
2. Copy the `custom_components/rv_internet_provider` directory into your HA `/config/custom_components/` directory. The final path must be `/config/custom_components/rv_internet_provider/manifest.json`, not a nested repository directory.
3. Restart Home Assistant to discover the new integration.
4. Open **Settings → Devices & services → Add integration → RV Internet Provider**.
5. Read the data-sharing notice and submit. HA checks the endpoint before creating the entry.
6. Add the ISP and Public IP entities to your dashboard. Use the integration's Options/Configure button to change the poll interval.

Only one entry is allowed because all queries originate from this HA server. Removing the integration through Devices & services removes its entities; remove the custom component directory separately if desired. Backups and recorder history may retain old data.

## HACS custom repository

Add `https://github.com/taylor-snow33/ha-internet-provider` in **HACS → menu → Custom repositories**, choose **Integration**, then download **RV Internet Provider** and restart HA. Continue with step 4 above. This repository contains `hacs.json` and the standard `custom_components` layout; it is not automatically included in HACS's default catalog.

## Failover and interpretation

- With normal failover, the ISP typically changes on the next successful poll after HA starts using the new connection. Detection is periodic, not instantaneous.
- This does not query UniFi WAN health, reveal all standby WANs or switch WANs. A VPN or policy route may return the VPN/route's provider instead. IPv4 and IPv6 can use different paths; this lookup reports whichever address family the HA request actually uses.
- ISP/organization names can reflect the underlying carrier, reseller infrastructure or an upstream network rather than a retail brand.
- IP geolocation is approximate and can be the carrier's point of presence hundreds of miles away. **It is not RV GPS.** This integration never changes HA's location, time zone, zones or device trackers.
- A failed lookup makes entities unavailable. That means the lookup failed, not necessarily that the RV is offline. Last known data must not be treated as current ISP information during an outage. Recovery repopulates the entities on a successful lookup.

## Privacy

IPWhois sees the public source IP of the HA request and its normal network metadata. No account token, router password, device identifier, precise GPS or UniFi credentials are sent. The HTTPS endpoint is fixed, TLS verification stays enabled and redirects are not followed. The integration makes no state-changing router or HA configuration calls.

Public IP and approximate location are visible in entity states/attributes and may be recorded by HA, included in backups, exposed by your dashboards or sent to third-party systems to which you expose these entities. Do not expose them publicly. Consider excluding the Public IP entity from Recorder if raw response history is unnecessary. Flags are URL/text data; the integration does not download the flag image. No diagnostic export or custom service is registered.

## Development

Use Python 3.14.2+ for the pinned HA version. In an isolated virtual environment:

```sh
pip install -r requirements-dev.txt
ruff check custom_components tests
ruff format --check custom_components tests
pytest -q
```

Tests mock the network and exercise real Home Assistant config entries, entities, failures, recovery and options reload. See `VALIDATION.md` for the exact verified environment/results. No live RV/production HA deployment or real failover test is implied by passing these tests.

## Sources

- [IPWhois documentation and free plan](https://ipwhois.io/documentation)
- [Home Assistant data coordinator](https://contributors.home-assistant.io/core/integrations/fetching-data/)
- [Home Assistant configuration flow](https://contributors.home-assistant.io/core/integrations/config-flow/)
- [Home Assistant options flow](https://contributors.home-assistant.io/core/integrations/options-flow/)
