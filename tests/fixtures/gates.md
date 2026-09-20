# Gates, as the sweep's filters read them

A frozen copy of the word lists the gates were compiled from before they moved
into source/gates.md, so the tests around them keep asserting the behavior they
were written against. A fresh instance has no source/gates.md until the setup skill
writes one, and the tests ship with the template, so they read this instead.

Prose belongs in the real file; this one is the lists and nothing else.

## wrong-metro

```
san francisco, "sf", bay area, remote, berkeley, oakland, emeryville,
alameda, walnut creek, fremont, hayward
```

## title-class

```
machine learning, "ml", "ai", data scien, applied scien, research scien,
data engineer, deep learning, "nlp", "llm", forward deployed, decision scien
```

## ic-seat

```
"manager", "director", "vp", vice president, head of, "chief", "intern",
internship, new grad
```

## tooling-or-gtm

```
platform, infrastructure, "infra", devops, "sre", reliability,
solutions architect, account executive, "sales", "gtm", go-to-market,
support engineer, support specialist, advocate, security, appsec, "soc",
recruiter, marketing, designer, "counsel", evaluator, partnerships, enablement
```

## foreign-remote

```
europe, "emea", "eu", "apac", united kingdom, "uk", london, ireland, dublin,
germany, berlin, munich, france, paris, spain, portugal, italy, austria,
vienna, switzerland, zurich, sweden, stockholm, denmark, norway, finland,
poland, romania, belgium, netherlands, amsterdam, czech, prague, hungary,
greece, bulgaria, turkey, ukraine, israel, tel aviv, "india", bengaluru,
singapore, japan, tokyo, korea, taiwan, china, shenzhen, hong kong, vietnam,
thailand, indonesia, philippines, brazil, argentina, chile, colombia,
costa rica, honduras, latin america, "latam", australia, new zealand, canada,
toronto, vancouver, south africa, nigeria, kenya, egypt, "uae", dubai
```

## in-us

```
united states, "us", "usa", u.s., san francisco, berkeley, oakland, bay area,
america, "pst", "california"
```
