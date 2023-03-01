from datetime import datetime, tzinfo, timedelta
import pytz

def _now():
    return datetime.utcnow().replace(tzinfo=pytz.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
    
def json_formatter(o):
    """Help format a dictionary to a JSON object.
    
    Note:
        I perform a conversion from a datetime object with a
        generic timezone to the UTC +00:00 default timezone.
        Then I replace the +00:00 with Z, as ISO8601 standard.
    """
        
    class TZ(tzinfo):
        """The default UTC +00:00 timezone."""
        def utcoffset(self, dt):
            return timedelta(hours=+0, minutes=+0)
        def dst(self, dt):
            return timedelta(hours=0)

    if isinstance(o, datetime):
        # Convert to UTC +00:00 datetime
        # TODO  consider o.astimezone(tz=TZ()) instead
        d = o.replace(tzinfo=TZ())
        # Convert to ISO 8601 standard
        return d.isoformat().replace('+00:00', 'Z')