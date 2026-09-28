import re

html = open(r"data\debug_pvr_20260924.html", encoding="utf-8").read()

targets = [
    "20260924",
    "showDate",
]

for target in targets:
    print("\n" + "=" * 70)
    print("TARGET:", target)
    print("=" * 70)

    positions = [m.start() for m in re.finditer(re.escape(target), html)]

    print("COUNT:", len(positions))

    for i, pos in enumerate(positions[:15]):
        print(f"\n--- OCCURRENCE {i + 1} ---")
        print(html[max(0, pos - 500):pos + 1000])
