Trained 6,000 episodes x 3 seeds per design vs. a 100%-skill monk, then tested in 1,000 games with exploration off.

| Design | Question | Test win | Caught | Timeout | Episodes to 70% | States |
|---|---|---|---|---|---|---|
| Baseline | the design used in the game | **100%** | 0% | 0% | 3,300 | 1,199 |
| No wall penalty | is the -5 for bumping walls needed? | **100%** | 0% | 0% | 3,400 | 1,011 |
| No step penalty | does -1 per move make it hurry? | **85%** | 7% | 9% | 5,800 (2 never) | 1,040 |
| Can't see the monk | how much does seeing the monk matter? | **17%** | 8% | 75% | never | 134 |
| Sees monk 1 square | smaller state - learns faster or worse? | **100%** | 0% | 0% | 2,833 | 633 |
| Can't see scroll spot | must it know where the scroll is? | **50%** | 0% | 50% | never | 373 |
| gamma = 0.5 | only cares about the near future | **97%** | 2% | 1% | 4,200 | 1,445 |
| alpha = 0.05 | learns in smaller steps | **90%** | 0% | 10% | 5,433 | 1,233 |
