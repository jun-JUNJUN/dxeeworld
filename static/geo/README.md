# GeoIP2 Database Setup

This directory contains the GeoIP2 Country database for IP-based locale detection.

## Required File

- `GeoLite2-Country.mmdb` - MaxMind GeoLite2 Country database

## How to Obtain the Database

1. Sign up for a free MaxMind account at: https://www.maxmind.com/en/geolite2/signup
2. Generate a license key in your account dashboard
3. Download GeoLite2 Country database (MMDB format)
4. Place the `GeoLite2-Country.mmdb` file in this directory

## Download Command (with license key)

```bash
# Replace YOUR_LICENSE_KEY with your actual MaxMind license key
wget "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-Country&license_key=YOUR_LICENSE_KEY&suffix=tar.gz" -O GeoLite2-Country.tar.gz
tar -xzf GeoLite2-Country.tar.gz
cp GeoLite2-Country_*/GeoLite2-Country.mmdb static/geo/
rm -rf GeoLite2-Country_* GeoLite2-Country.tar.gz
```

## Alternative: Automatic Updates

For production environments, consider setting up automatic monthly updates using MaxMind's GeoIP Update tool:
https://github.com/maxmind/geoipupdate

## Testing Without Real Database

For development/testing purposes, you can create a minimal test database or mock the service.
See `tests/test_locale_detection_service.py` for mocking examples.

## Database Updates

- Update frequency: Monthly (recommended)
- The database should be updated to maintain accuracy of IP geolocation
- File size: Approximately 5-7 MB

## License

GeoLite2 databases are distributed under the Creative Commons Attribution-ShareAlike 4.0 International License.
