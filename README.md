# jewish
Pure-Python implementations of calculations related to Judaism

Example:
```python
import datetime
import jewish

today = datetime.date.today()
jewish_today = jewish.JewishDate.from_date(today)
rosh_hashannah = jewish.JewishDate(jewish_today.year + 1, 1, 1)
days_to_rh = rosh_hashannah.to_sdn() - jewish_today.to_sdn()

print 'Today is %s in the secular calendar and %s in the Jewish calendar.' % (today, jewish_today)
print 'Rosh HaShannah is on %s, which is in %s days.' % (rosh_hashannah.to_date(), days_to_rh)
```

Outputs:
```
Today is 2016-08-17 in the secular calendar and 13 Av 5776 in the Jewish calendar.
Rosh HaShannah is on 2016-10-03, which is in 47 days.
```

## Compatibility
jewish works with Python 2.7 and Python 3.
