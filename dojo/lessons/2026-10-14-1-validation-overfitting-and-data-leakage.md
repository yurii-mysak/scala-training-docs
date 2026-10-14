---
id: 2026-10-14-1
date: 2026-10-14
day: 9
slot: core
track: ai-ml
domain: ai-ml
rung: ai-ml-03
level: B
title: Validation, overfitting and data leakage
est_min: 30
files_to: 24-ai-ml-foundations
status: sent
sent_at: 2026-10-14T05:55:55Z
marked_at: null
filed_to: null
review_due: null
sources:
- title: Kaggle Learn — Intro to Machine Learning
  url: https://www.kaggle.com/learn/intro-to-machine-learning
- title: Kaggle Learn — Intermediate Machine Learning
  url: https://www.kaggle.com/learn/intermediate-machine-learning
- title: 'StatQuest — Machine Learning Fundamentals: Bias and Variance'
  url: https://statquest.org/video-index/
---
# Validation, overfitting and data leakage

> AI / ML foundations · Beginner · ~30 min · rung 3 of 38 · needs: Your first model: Scala collections in, predictions out (ai-ml-02)

## Why this matters
You now have a fitted model, and the first number it hands you — its error on the rows it was trained on — is the one number that cannot tell you whether it works.
Every ML incident you will ever triage as a Product Owner reduces to one of two bugs in this lesson: a model chosen on a score it had already seen, or a feature that quietly carries the answer.
It sits here because every rung above it — regularisation, hyper-parameter search, evaluating an LLM — is a variation on "hold something back and measure on that".

## The idea

A model's error on its own training rows measures how much of that table it managed to store, not how well it predicts. Push its capacity high enough and that error goes to zero while the model gets worse at the only job it has. The scikit-learn user guide states the trap in one sentence:

> "Learning the parameters of a prediction function and testing it on the same data is a methodological mistake: a model that would just repeat the labels of the samples that it has just seen would have a perfect score but would fail to predict anything useful on yet-unseen data."
> — scikit-learn developers, *3.1. Cross-validation: evaluating estimator performance*, scikit-learn 1.9.1 documentation, accessed 2026-10-14, https://scikit-learn.org/stable/modules/cross_validation.html

The fix is procedural, not mathematical: hold rows back.

### Three sets, and what each is for

- **Training set** (60–80% of rows): what the model fits its parameters on.
- **Validation set** (10–20%): what you score candidates on — this k against that one, these features against those. You look at it many times.
- **Test set** (10–20%): what the chosen model is scored on once, at the end, for a number you can quote.

> "You should test a model against a different set of examples than those used to train the model."
> — Google for Developers, *Datasets: Dividing the original dataset*, Machine Learning Crash Course, 2025-12-03, https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets

Why three and not two: every time you pick something because a score was better, you fit a little to that set. The same page warns that "the more often you use the same test set, the more likely the model closely fits the test set" (Google for Developers, Machine Learning Crash Course, "Datasets: Dividing the original dataset"); CS231n puts it as a rule: "we cannot use the test set for the purpose of tweaking hyperparameters" (Stanford CS231n, "Image Classification", §"Validation sets for Hyperparameter tuning"). The validation set absorbs that wear; the test set stays sealed:

```mermaid
flowchart TB
  D["all labelled rows"] --> S["seeded shuffle, then split"]
  S --> TR["training set 60–80%"]
  S --> VA["validation set 10–20%"]
  S --> TE["test set 10–20%, sealed"]
  TR -->|"fit parameters and scalers"| M["candidate models k = 100 … 1"]
  M -->|"score each, many times"| VA
  VA -->|"keep the best"| C["chosen model"]
  C -->|"score once"| TE
  TE --> R["the number you report"]
```

*Figure 1: Fit on training rows, choose on validation rows, report once on the sealed test set. Adapted from Google for Developers, https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets*

A split is a seeded shuffle and a slice. Shuffle, because tables arrive sorted — by date, say — so slicing gives you two populations rather than two samples of one. Seed, because the split must be identical for every candidate; otherwise you rank models by the split they happened to get. Ten row ids, sorted by date:

```scala
// file: Split.scala
import scala.util.Random
@main def split(): Unit =
  val rows = (1 to 10).toVector                 // row ids of a table that arrived sorted by date
  println(s"slice, no shuffle: validation+test = ${rows.drop(6)}")
  val shuffled = new Random(7).shuffle(rows)    // seeded: identical on every run
  val (train, rest) = shuffled.splitAt(6)
  val (valid, test) = rest.splitAt(2)
  println(s"train=$train  validation=$valid  test=$test")
  println(s"rerun with seed 7 -> validation=${new Random(7).shuffle(rows).slice(6, 8)}")
```

```text
slice, no shuffle: validation+test = Vector(7, 8, 9, 10)
train=Vector(1, 2, 10, 4, 8, 5)  validation=Vector(9, 6)  test=Vector(3, 7)
rerun with seed 7 -> validation=Vector(9, 6)
```

Without the shuffle the held-out rows are just the four newest — a different population. With it each set mixes old and new, and seed 7 returns the same validation rows `(9, 6)` on every run.

**The QA reading.** The validation set is a test suite the model must never see during development; the test set is the acceptance run before release. Tune code until the suite goes green and the suite stops measuring correctness.

### Capacity decides which way you fail

**Capacity** is how much structure a model can represent. For k-nearest neighbours (k-NN), where a prediction is the average target of the k closest training rows, capacity is 1/k: at k = 1 it reproduces its training rows exactly, at k = N (all rows) it predicts one constant for everything.

**Underfitting** (high **bias**): too little capacity for the real pattern, so the model is wrong in the same direction across whole regions and error is high on training *and* validation rows. **Overfitting** (high **variance**): enough capacity to fit the noise in the rows it happened to see, so training error collapses towards zero while validation error climbs, and a different sample would have produced a visibly different model (StatQuest, "Machine Learning Fundamentals: Bias and Variance"). Forty points on the line y = 2x, each with noise of standard deviation 2, scored by 1-D k-NN:

```scala
// file: Overfit.scala
type Rows = Vector[(Double, Double)]
@main def overfit(): Unit =
  val g = new scala.util.Random(1)
  def point(x: Double) = (x, 2 * x + g.nextGaussian() * 2) // truth: y = 2x, noise sd 2
  def draw(n: Int): Rows = Vector.fill(n)(point(g.nextDouble() * 10))
  val (train, valid) = (draw(40), draw(40))
  def knn(x: Double, k: Int) = train.sortBy((a, _) => math.abs(a - x)).take(k).map(_._2).sum / k
  def mae(rows: Rows, k: Int) = rows.map((x, y) => math.abs(knn(x, k) - y)).sum / rows.size
  for k <- List(40, 10, 3, 1) do
    println(f"k=$k%2d   train MAE ${mae(train, k)}%5.2f   validation MAE ${mae(valid, k)}%5.2f")
```

```text
k=40   train MAE  4.90   validation MAE  5.58
k=10   train MAE  1.69   validation MAE  2.09
k= 3   train MAE  1.32   validation MAE  2.35
k= 1   train MAE  0.00   validation MAE  2.50
```

MAE (mean absolute error) averages |predicted − actual|; lower is better. k = 40 predicts one constant for every x: underfit, bad on both sets. k = 1 scores a perfect 0.00 on training rows — each row's nearest neighbour is itself — yet loses on validation (2.50) to k = 10 (2.09). Training error falls monotonically with capacity; validation error is U-shaped, and its bottom is what you ship. The lab runs the same sweep on 300 houses:

![Train and validation MAE against k for k-NN on 300 houses](assets/2026-10-14-1-chart-1.png)

*Figure 2: Train MAE falls to 0.000 at k = 1; validation MAE bottoms out at k = 3 (18.868) — Kaggle Learn's underfitting/overfitting curve (Intro to ML, Lesson 5) on this lesson's data. Generated from the lab output (Step 4).*

### k-fold cross-validation: a steadier number

One 80/20 split estimates from few rows and withholds them from training. **k-fold cross-validation** reuses everything: cut the data into k equal folds, train on k−1 and score on the one held out, rotating until every fold has been held out exactly once. (This k counts folds; it is unrelated to the k of k-NN.) "The performance measure reported by k-fold cross-validation is then the average of the values computed in the loop" (scikit-learn 1.9.1 user guide, §3.1 "Cross-validation: evaluating estimator performance"), and the spread across folds says how much to trust it. Assigning folds by row index mod 5 is enough:

```scala
// file: Folds.scala
@main def folds(): Unit =
  val rows = (0 until 10).toVector
  for f <- 0 until 5 do
    val hold = rows.filter(_ % 5 == f)
    val rest = rows.filter(_ % 5 != f)
    println(s"fold $f: train on ${rest.mkString(",")}   score on ${hold.mkString(",")}")
```

```text
fold 0: train on 1,2,3,4,6,7,8,9   score on 0,5
fold 1: train on 0,2,3,4,5,7,8,9   score on 1,6
fold 2: train on 0,1,3,4,5,6,8,9   score on 2,7
fold 3: train on 0,1,2,4,5,6,7,9   score on 3,8
fold 4: train on 0,1,2,3,5,6,7,8   score on 4,9
```

Every row is scored exactly once. scikit-learn draws the same rotation, test set kept outside:

![scikit-learn diagram: training data split into 5 folds, each fold held out once, test data kept for final evaluation](assets/2026-10-14-1-fig-1.png)

*Figure 3: 5-fold cross-validation for choosing parameters, with a separate test set for the final evaluation. Source: scikit-learn developers, [3.1. Cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) (BSD-3-Clause).*

The trade, in the same guide: "This approach can be computationally expensive, but does not waste too much data (as is the case when fixing an arbitrary validation set)" (scikit-learn 1.9.1 user guide, §3.1 "Cross-validation: evaluating estimator performance") — k fits instead of one, for an estimate averaged over all your rows. k = 5 or 10 is usual, and small datasets are where it earns its cost. It replaces the validation split, not the test set. CS231n plots this for choosing the k of k-NN — a dot per fold, a line through the means:

![CS231n plot: cross-validation accuracy for each k of k-NN, five points per k, trend line through the means with error bars](assets/2026-10-14-1-fig-2.png)

*Figure 4: "Example of a 5-fold cross-validation run for the parameter k" (accuracy, higher is better); "a value of about k = 7 works best on this particular dataset". Source: Stanford CS231n, Andrej Karpathy, [Image Classification](https://cs231n.github.io/classification/) (MIT).*

### Data leakage: the bug that makes all of this worthless

"Data leakage occurs when information that would not be available at prediction time is used when building the model" (scikit-learn 1.9.1 user guide, §12.2 "Data leakage"). Two shapes.

**Target leakage** is a feature that is a consequence of the answer rather than a cause of it: predicting pneumonia from a `took_antibiotics` column, churn from a `contract_closed_date`, a default from the collections-team flag. It scores beautifully on every split, because the column really does determine the target in your table — and it is empty or wrong at the moment you need the prediction (Kaggle Learn, Intermediate Machine Learning, Lesson 7 "Data Leakage"). A house's stamp duty is 2% of its sale price and is paid after the sale:

```scala
// file: Leak.scala
type Row = (Double, Double, Double) // (size, price, stampDuty paid AFTER the sale)
@main def leak(): Unit =
  val g = new scala.util.Random(3)
  def house(size: Double): Row =
    val price = 3 * size + g.nextGaussian() * 20
    (size, price, price * 0.02 + g.nextGaussian() * 0.1)
  val (tr, va) = Vector.fill(200)(house(40 + g.nextDouble() * 160)).splitAt(150)
  def nearest(f: Row => Double, r: Row) = tr.minBy(t => math.abs(f(t) - f(r))) // 1-NN, one feature
  def mae(f: Row => Double) = va.map(r => math.abs(nearest(f, r)._2 - r._2)).sum / va.size
  println(f"1-NN on size       (known before the sale): validation MAE ${mae(_._1)}%6.2f")
  println(f"1-NN on stampDuty  (known only after it):   validation MAE ${mae(_._3)}%6.2f")
```

```text
1-NN on size       (known before the sale): validation MAE  24.61
1-NN on stampDuty  (known only after it):   validation MAE   7.02
```

The split is clean, yet the leaked model "wins" 7.02 to 24.61 — the column is the price divided by 50. When you must price a house, it is empty; the lab's Step 6 measures the cost.

**Train–test contamination** is a clean split undone by preprocessing fitted on all the rows. Standardise a column by its mean over all 300 rows, then split, and the mean each training row was scaled by is a function of the validation rows too. Hence the order: "Always split the data into train and test subsets first, particularly before any preprocessing steps" (scikit-learn 1.9.1 user guide, §12.2.1 "How to avoid data leakage"). Both leak paths beside the honest one:

```mermaid
flowchart TB
  subgraph H["honest"]
    direction LR
    H1["all rows"] --> H2["split"] --> H3["fit scaler on<br/>training rows only"] --> H4["train"] --> H5["validation score<br/>= production score"]
  end
  subgraph C["contamination"]
    direction LR
    C1["all rows"] --> C2["fit scaler on<br/>ALL rows"] --> C3["split"] --> C4["training features already<br/>carry validation statistics"]
  end
  subgraph T["target leakage"]
    direction LR
    T1["column filled in after<br/>the outcome: stampDuty"] --> T2["validation score<br/>too good"] --> T3["column empty at<br/>prediction time"]
  end
  H ~~~ C ~~~ T
```

*Figure 5: The honest pipeline beside both leak paths. Adapted from scikit-learn 1.9.1 user guide §12.2, https://scikit-learn.org/stable/common_pitfalls.html*

Either way validation looks suspiciously good and production does not. A score that looks too good is a bug report, not a result.

## Lab

**The question this lab answers:** as you dial a model's capacity from "one constant for everybody" to "memorise every row", what happens to its error on the training rows and on held-out rows, and which number would you have believed? And when a column that is only known after the sale sneaks into the features, how far apart do the validation score and the production score drift?

The sources for this rung are Python courses (Kaggle, scikit-learn, CS231n); the lab does the work in Scala 3 with the standard library only — 300 synthetic houses, a hand-written 80/20 split, and k-nearest-neighbour regression, whose capacity is a single integer you can turn.

### Step 1 — generate the data and split it before touching anything

A seeded `scala.util.Random` makes the whole run reproducible. The true rule is `price = 3·size + 20·rooms`, plus Gaussian noise with a standard deviation of 20 that no model can ever learn — the floor on every error below.

```scala
val gen = new Random(42)
val houses = Vector.fill(300) {
  val size  = 40.0 + gen.nextDouble() * 160.0   // 40..200 square metres
  val rooms = 1 + gen.nextInt(6)                // 1..6
  val noise = gen.nextGaussian() * 20.0         // irreducible
  House(size, rooms, 3.0 * size + 20.0 * rooms + noise)
}
val shuffled = new Random(7).shuffle(houses)
val (trainH, valH) = shuffled.splitAt(240)      // split FIRST
```

Only then is the scaler computed, from the 240 training rows alone. Computing `mean` and `sd` over all 300 rows first would be exactly the train–test contamination described above.

### Step 2 — k-nearest neighbours, three functions

No training step: the model *is* the training rows. A prediction sorts them by distance in standardised feature space, takes the k closest, and averages their prices. The error measure is **MAE**, mean absolute error — the average of `|predicted − actual|`, in the same units as price, lower is better.

```scala
def predict(base: Vector[(Vector[Double], Double)], x: Vector[Double], k: Int): Double =
  base.map((f, p) => (dist(f, x), p)).sortBy(_._1).take(k).map(_._2).sum / k
```

At k = 1 the nearest training row to a training row is itself, at distance 0, so the prediction is its own price and the training error is exactly 0.

### Step 3 — the whole program

```scala
// file: Lab.scala
import scala.util.Random

final case class House(size: Double, rooms: Int, price: Double)

@main def lab(): Unit =
  // ---- Step 1: 300 synthetic houses from one seed -------------------------
  val gen = new Random(42)
  val houses = Vector.fill(300) {
    val size  = 40.0 + gen.nextDouble() * 160.0   // 40..200 square metres
    val rooms = 1 + gen.nextInt(6)                // 1..6
    val noise = gen.nextGaussian() * 20.0         // irreducible: no model can learn this
    House(size, rooms, 3.0 * size + 20.0 * rooms + noise)
  }
  println("first 3 generated houses:")
  houses.take(3).foreach(h =>
    println(f"  size=${h.size}%6.2f  rooms=${h.rooms}  price=${h.price}%7.2f"))

  // ---- Step 2: shuffle and split 80/20 BEFORE any preprocessing -----------
  val shuffled = new Random(7).shuffle(houses)
  val (trainH, valH) = shuffled.splitAt(240)
  println(f"%ntrain=${trainH.size} rows   validation=${valH.size} rows")

  def mean(xs: Seq[Double]): Double = xs.sum / xs.size
  def sd(xs: Seq[Double]): Double =
    val m = mean(xs); math.sqrt(xs.map(x => (x - m) * (x - m)).sum / xs.size)

  // scaler fitted on TRAIN ONLY — fitting it on all 300 rows would be leakage
  val (muSize, sdSize)   = (mean(trainH.map(_.size)),          sd(trainH.map(_.size)))
  val (muRooms, sdRooms) = (mean(trainH.map(_.rooms.toDouble)), sd(trainH.map(_.rooms.toDouble)))
  println(f"scaler from train only: size mu=$muSize%.3f sd=$sdSize%.3f | rooms mu=$muRooms%.3f sd=$sdRooms%.3f")

  def feats(h: House): Vector[Double] =
    Vector((h.size - muSize) / sdSize, (h.rooms - muRooms) / sdRooms)
  val train = trainH.map(h => (feats(h), h.price))
  val valid = valH.map(h => (feats(h), h.price))

  // ---- Step 3: k-nearest-neighbour regression ----------------------------
  def dist(a: Vector[Double], b: Vector[Double]): Double =
    math.sqrt(a.lazyZip(b).map((x, y) => (x - y) * (x - y)).sum)

  def predict(base: Vector[(Vector[Double], Double)], x: Vector[Double], k: Int): Double =
    base.map((f, p) => (dist(f, x), p)).sortBy(_._1).take(k).map(_._2).sum / k

  def mae(base: Vector[(Vector[Double], Double)], eval: Vector[(Vector[Double], Double)], k: Int): Double =
    mean(eval.map((f, p) => math.abs(predict(base, f, k) - p)))

  // one prediction traced by hand, so the arithmetic is visible
  val (vx, vy) = valid.head
  val near3 = train.map((f, p) => (dist(f, vx), p)).sortBy(_._1).take(3)
  println(f"%ntraced: validation row 0, actual price ${vy}%.2f")
  near3.zipWithIndex.foreach { case ((d, p), i) =>
    println(f"  neighbour ${i + 1}: distance=$d%.4f  price=$p%.2f") }
  println(f"  k=3 prediction = (${near3.map(_._2).map(p => f"$p%.2f").mkString(" + ")}) / 3 = ${near3.map(_._2).sum / 3}%.2f")
  println(f"  absolute error = ${math.abs(near3.map(_._2).sum / 3 - vy)}%.2f")

  // ---- Step 4: the capacity sweep ---------------------------------------
  println(f"%n  k   capacity    train MAE   validation MAE")
  val ks = List(100, 30, 10, 3, 1)
  val scored = ks.map { k =>
    val tr = mae(train, train, k)
    val va = mae(train, valid, k)
    val label = if k >= 30 then "low" else if k >= 10 then "medium" else "high"
    println(f"$k%3d   $label%-9s   $tr%9.3f   $va%14.3f")
    (k, va)
  }
  val best = scored.minBy(_._2)
  println(f"%nbest k by validation MAE: k=${best._1} at MAE ${best._2}%.3f")
  println(f"in-sample MAE of k=1: ${mae(train, train, 1)}%.3f   <- it memorises")
  println(f"validation MAE of k=1: ${mae(train, valid, 1)}%.3f   <- what it is really worth")

  // ---- Step 5: 5-fold cross-validation, folds by row index mod 5 ---------
  println(f"%n5-fold cross-validation over all 300 rows (fold = index mod 5)")
  println("  k    f0       f1       f2       f3       f4      mean")
  val all = shuffled.zipWithIndex
  ks.foreach { k =>
    val perFold = (0 until 5).map { f =>
      val hold = all.filter(_._2 % 5 == f).map(_._1)
      val rest = all.filter(_._2 % 5 != f).map(_._1)
      val mS = mean(rest.map(_.size)); val dS = sd(rest.map(_.size))
      val mR = mean(rest.map(_.rooms.toDouble)); val dR = sd(rest.map(_.rooms.toDouble))
      def ft(h: House) = Vector((h.size - mS) / dS, (h.rooms - mR) / dR)
      mae(rest.map(h => (ft(h), h.price)), hold.map(h => (ft(h), h.price)), k)
    }
    println(f"$k%3d " + perFold.map(x => f"$x%8.3f").mkString + f"  ${mean(perFold)}%8.3f")
  }

  // ---- Step 6: target leakage — a column that is only filled in AFTER the sale
  val dutyGen = new Random(99)                    // separate seed: houses above are unchanged
  val duty = shuffled.map(h => h.price * 0.02 + dutyGen.nextGaussian() * 0.1)  // stamp duty = 2% of price
  val (dTr, dVa) = duty.splitAt(240)
  val (muD, sdD) = (mean(dTr), sd(dTr))           // scaled on train only, like the rest
  def withDuty(rows: Vector[(Vector[Double], Double)], d: Seq[Double]) =
    rows.zip(d).map { case ((f, p), x) => (f :+ (x - muD) / sdD, p) }
  val trainL = withDuty(train, dTr)
  val validL = withDuty(valid, dVa)
  val prodL  = withDuty(valid, dVa.map(_ => muD)) // at prediction time duty is unknown: fill with the mean
  println(f"%ntarget leakage: feature stampDuty (2%% of price) added")
  println("  k   honest validation   leaked validation   leaked model in production")
  ks.foreach(k => println(f"$k%3d   ${mae(train, valid, k)}%17.3f   ${mae(trainL, validL, k)}%17.3f   ${mae(trainL, prodL, k)}%26.3f"))
```

Run it with `scala Lab.scala`.

### Step 4 — the single split: data, one traced prediction, and the capacity sweep

```text
first 3 generated houses:
  size=156.41  rooms=1  price= 494.57
  size=112.20  rooms=1  price= 346.10
  size= 84.12  rooms=1  price= 249.12

train=240 rows   validation=60 rows
scaler from train only: size mu=116.380 sd=46.690 | rooms mu=3.404 sd=1.612

traced: validation row 0, actual price 464.71
  neighbour 1: distance=0.0948  price=472.36
  neighbour 2: distance=0.0990  price=508.85
  neighbour 3: distance=0.1302  price=501.20
  k=3 prediction = (472.36 + 508.85 + 501.20) / 3 = 494.14
  absolute error = 29.43

  k   capacity    train MAE   validation MAE
100   low            49.816           51.406
 30   low            22.936           25.661
 10   medium         18.805           20.219
  3   high           13.675           18.868
  1   high            0.000           20.995

best k by validation MAE: k=3 at MAE 18.868
in-sample MAE of k=1: 0.000   <- it memorises
validation MAE of k=1: 20.995   <- what it is really worth
```

**Verdict:** the training column falls all the way to 0.000 and is therefore useless as a ranking signal — it would have chosen k = 1, only third of five on held-out rows. The validation column is U-shaped and picks k = 3 at MAE 18.868. The honest cost of believing the in-sample number is 20.995 − 18.868 = 2.127 price units of avoidable error on every future prediction, bought with a score of exactly zero.

### Step 5 — five folds instead of one split

```text
5-fold cross-validation over all 300 rows (fold = index mod 5)
  k    f0       f1       f2       f3       f4      mean
100   48.973  46.309  49.346  59.373  52.858    51.372
 30   23.611  23.530  23.802  28.039  23.311    24.459
 10   17.993  20.078  20.439  19.231  23.109    20.170
  3   19.486  18.563  22.275  21.565  21.205    20.619
  1   23.725  23.890  25.214  24.269  27.129    24.845
```

**Verdict:** cross-validation reverses the winner. On the single split k = 3 (18.868) beat k = 10 (20.219); averaged over five folds k = 10 (20.170) beats k = 3 (20.619). The per-fold columns say why: for k = 3 the five estimates run from 18.563 to 22.275, a spread of 3.712, so a gap of 1.351 between the two candidates on one split was inside the noise. Five fits bought a decision the one split got wrong.

![Per-fold validation MAE for k = 30, 10, 3, 1 with a line through the five-fold means](assets/2026-10-14-1-chart-3.png)

*Figure 6: Each dot is one held-out fold, the line joins the five-fold means; k = 10 (mean 20.170) edges out k = 3 (20.619), whose folds alone span 18.563–22.275 — the CS231n plot of Figure 4, for house prices. k = 100 (mean 51.372) is left off so the spread stays readable. Generated from the lab output (Step 5).*

### Step 6 — the same model with a leaked column

The last block adds one feature, `stampDuty`: 2% of the sale price plus a little noise, standardised with training-only statistics like the others, so the split and the scaling are both clean. Three scores per k: the honest model on validation rows (Step 4's column), the leaked model on validation rows, and the leaked model "in production", where the duty is not yet known and is filled with its training mean.

```text
target leakage: feature stampDuty (2% of price) added
  k   honest validation   leaked validation   leaked model in production
100              51.406              38.727                       65.845
 30              25.661              16.294                       60.714
 10              20.219              11.056                       61.388
  3              18.868              11.072                       63.803
  1              20.995              10.945                       68.811
```

![Honest validation, leaked validation and leaked production MAE for each k](assets/2026-10-14-1-chart-2.png)

*Figure 7: With the leaked column every k looks better on validation (≈11 instead of ≈19–21), and every k is far worse once the column is empty (61–69). Generated from the lab output (Step 6).*

**Verdict:** judged by validation MAE the leaked model wins at every k — 10.945 at k = 1 against the honest best of 18.868 — and you would ship it. In production it scores 68.811 at that same k, 3.6 times the honest model's validation error. Nothing in the validation number warned you; only asking "is this column known at prediction time?" does.

### Reading the output

**What each column means.** `k` is the number of neighbours averaged, so capacity is 1/k — k = 100 is the lowest-capacity model in the table, k = 1 the highest. `capacity` is just that label. `train MAE` is mean absolute error scored on the same 240 rows the model holds; `validation MAE` is scored on the 60 rows it has never seen. Both are in price units, and **lower is better** — but only the validation column is an estimate of anything. In the cross-validation table, `f0`…`f4` are the five held-out folds of 60 rows each, and `mean` is their average; lower is better, and a wide spread across f0…f4 means the estimate itself is shaky.

| k | capacity | train MAE | validation MAE | 5-fold mean |
|---|---|---|---|---|
| 100 | low | 49.816 | 51.406 | 51.372 |
| 30 | low | 22.936 | 25.661 | 24.459 |
| 10 | medium | 18.805 | 20.219 | **20.170** |
| 3 | high | 13.675 | **18.868** | 20.619 |
| 1 | high | **0.000** | 20.995 | 24.845 |

**The arithmetic, traced.** Take validation row 0, whose true price is 464.71. Its three nearest training rows sit at distances 0.0948, 0.0990 and 0.1302 in standardised feature space (very close: all four houses are near-identical in size and rooms) and carry prices 472.36, 508.85 and 501.20. The k = 3 prediction is their plain mean: (472.36 + 508.85 + 501.20) / 3 = 1482.41 / 3 = 494.14. The absolute error is |494.14 − 464.71| = 29.43, and the validation MAE 18.868 is that calculation averaged over all 60 validation rows. Note what the error is made of: those three neighbours are nearly the same house, so their prices differ by up to 508.85 − 472.36 = 36.49 purely through the Gaussian noise of standard deviation 20 that was added when the data was generated. When neighbours are that close, the error on a new house is roughly its own noise minus the average noise of its k neighbours, with standard deviation 20 × √(1 + 1/k), and the mean absolute value of a Gaussian is about 0.8 × its standard deviation. For k = 3: 20 × √(4/3) = 23.09, × 0.8 ≈ 18.5 (measured: 18.868). For k = 1: 20 × √2 = 28.28, × 0.8 ≈ 22.6 (measured: 20.995). Even a perfect model would score 0.8 × 20 = 16. That is why the U has a floor near 19 and not near 0.

**The leak table.** `honest validation` is Step 4's validation column; `leaked validation` is the same k-NN with `stampDuty` as a third feature, scored on the same 60 rows; `leaked model in production` is that model scored on those rows with the duty replaced by its training mean, because the duty does not exist before the sale. Lower is better in all three; the gap between the leaked-validation and production columns is the size of the lie. At k = 3: the leak "improves" validation by 18.868 − 11.072 = 7.796, and production comes in at 63.803 − 18.868 = 44.935 worse than the honest model's estimate, a factor of 63.803 / 18.868 = 3.38.

**Why k = 1 scores 0.000 in-sample.** Score a training row against the training set and its nearest neighbour is itself, at distance exactly 0, so the predicted price is its own recorded price and |predicted − actual| = 0 for all 240 rows. Nothing was learned; the table was indexed.

### Cause → mechanism → consequence → practice

1. **Cause.** You score a model on rows it was fitted on.
2. **Mechanism.** Capacity above what the signal needs gets spent on the noise in those particular rows — at k = 1 the model is a lookup table over them — so in-sample error falls to 0.000 while the function it represents gets further from the real one.
3. **Consequence.** The in-sample ranking is inverted: it crowns k = 1, which is only third of five on held-out rows (20.995 against 18.868). A leaked column does the same to the held-out ranking: it makes every k look better on validation (≈11) and every k worse in production (61–69).
4. **What it means in practice.** Split first, with a fixed seed, before any preprocessing; fit every transformation on training rows only; choose hyper-parameters on validation rows or by k-fold cross-validation and report the spread, not just the mean; and keep one test set sealed for a single final number. When a score looks too good, go looking for the feature that already knows the answer.

## Self-check
1. A colleague reports that his gradient-boosted model reaches 99.4% accuracy and asks whether you can ship it. What is the first question you ask, and why is it not "which metric"? <details><summary>Answer</summary>"Which rows was that measured on, and had the model been fitted on any of them?" A score on training rows measures storage, not prediction — a high-capacity model can drive it to zero by memorising, as k = 1 did in the lab (in-sample MAE 0.000, held-out 20.995). Only after the number is known to come from held-out rows is the metric worth discussing. The follow-up question is leakage: 99.4% is high enough to suspect a feature that is a consequence of the target, available in the training table but not at prediction time.</details>
2. You have 300 labelled rows, five candidate models, and a validation MAE for each from one 80/20 split; the best two differ by 1.4. Why is that not enough to choose, and what do you do instead? <details><summary>Answer</summary>The estimate comes from 60 rows, so its own uncertainty can be larger than the gap. In the lab k = 3 beat k = 10 by 1.351 on the single split, but the five-fold means reversed the order (20.619 against 20.170), and the per-fold spread for k = 3 — 18.563 to 22.275 — showed the gap was inside the noise. Use k-fold cross-validation: k = 5 or 10 folds, every row held out exactly once, report mean and spread. It costs k fits instead of one, which is exactly the trade you want when data is scarce rather than compute.</details>
3. The pipeline standardises every numeric column by subtracting the column mean and dividing by the standard deviation, then shuffles and splits 80/20. Name the bug, say which direction it moves the validation score, and give the fix. <details><summary>Answer</summary>Train–test contamination, a form of data leakage: the means and standard deviations were computed over all rows, so every training feature was scaled using statistics that encode the held-out rows. The validation score comes out optimistic, because the model was handed information it will not have in production, and the gap shows up only after release. The fix is the order: split first, compute the statistics on training rows only, then apply those same fixed numbers to the validation, test and production rows — what the lab does with `muSize` and `sdSize` from `trainH` alone. Inside cross-validation the scaler must be refitted inside every fold, as the lab's fold loop does.</details>

## Sources
- [scikit-learn 1.9.1 user guide — 3.1. Cross-validation: evaluating estimator performance](https://scikit-learn.org/stable/modules/cross_validation.html) — scikit-learn developers — the quoted definition of the "test on the same data" mistake, the k-fold procedure and the "average of the values computed in the loop" rule, and the quoted cost/data trade-off of cross-validation ("This approach can be computationally expensive, but does not waste too much data…", §3.1 introduction); Figure 3 is the guide's `grid_search_cross_validation.png` from github.com/scikit-learn/scikit-learn `doc/images/` (BSD-3-Clause) (accessed 2026-10-14 and 2026-10-15).
- [scikit-learn 1.9.1 user guide — 12. Common pitfalls and recommended practices](https://scikit-learn.org/stable/common_pitfalls.html) — scikit-learn developers — §12.2 "Data leakage": the definition used in this lesson, and §12.2.1 "How to avoid data leakage" for the split-before-preprocessing rule (accessed 2026-10-14).
- [Google for Developers — Machine Learning Crash Course, "Datasets: Dividing the original dataset"](https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets) — Google for Developers, last updated 2025-12-03 — the quoted rule on testing against different examples, the three-way train/validation/test split, and the warning that repeatedly reused test sets wear out (accessed 2026-10-14).
- [Kaggle Learn — Intro to Machine Learning](https://www.kaggle.com/learn/intro-to-machine-learning) — Lesson 4 "Model Validation" and Lesson 5 "Underfitting and Overfitting": the curriculum shape of this rung — held-out MAE, and tree depth as the capacity dial behind the U-shaped curve (accessed 2026-10-14; the course pages require a logged-in session, so no passage is quoted from them here).
- [Kaggle Learn — Intermediate Machine Learning](https://www.kaggle.com/learn/intermediate-machine-learning) — Lesson 5 "Cross-Validation" and Lesson 7 "Data Leakage": the advice that k-fold cross-validation earns its cost on small datasets, and the target-leakage examples (`took_antibiotics`, a closed-contract date) retold here in Scala terms (accessed 2026-10-14; logged-in session required, so no passage is quoted).
- [Stanford CS231n — Image Classification](https://cs231n.github.io/classification/) — Andrej Karpathy, CS231n course notes — §"Validation sets for Hyperparameter tuning": the quoted rule that the test set cannot be used to tweak hyper-parameters, and Figure 4 (`assets/cvplot.png` from github.com/cs231n/cs231n.github.io, MIT licence) with its quoted caption (accessed 2026-10-15).
- [StatQuest — Machine Learning Fundamentals: Bias and Variance](https://statquest.org/video-index/) — Josh Starmer — the bias/variance vocabulary attached to the two ends of the capacity axis: underfitting as consistent error, overfitting as sensitivity to the particular sample (accessed 2026-10-14, via the video index).

## Next on this track
Next on AI / ML foundations: **Vectors and matrices as data** (rung 4 of 38, Beginner).
