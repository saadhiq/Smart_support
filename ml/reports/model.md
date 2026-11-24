# Category classifier

## Model

`normalise()` -> FeatureUnion(word 1-2-gram TF-IDF, char_wb 3-5-gram TF-IDF,
both sublinear_tf) -> LogisticRegression(max_iter=2000, class_weight="balanced").

Train 18,773 rows, test 4,751 rows (grouped split, see split.md).
scikit-learn 1.9.1.

## Choosing C (GroupKFold, 5 folds, training set only)

| C | cv macro-F1 mean | cv macro-F1 std |
|---|---|---|
| 0.5 | 0.9984 | 0.0007 |
| 1.0 | 0.9986 | 0.0006 |
| 2.0 | 0.9989 | 0.0005 |
| 5.0 | 0.999 | 0.0004 |

Best C: **5**. The model was then refit on all of train.

## Test set (evaluated once)

- Accuracy: **0.9996**
- Macro-F1: **0.9995**

### Per class

| class | precision | recall | f1-score | support |
|---|---|---|---|---|
| ACCOUNT | 1.0 | 1.0 | 1.0 | 1010.0 |
| CANCEL | 1.0 | 1.0 | 1.0 | 185.0 |
| CONTACT | 1.0 | 1.0 | 1.0 | 387.0 |
| DELIVERY | 0.997 | 0.997 | 0.997 | 323.0 |
| FEEDBACK | 1.0 | 1.0 | 1.0 | 397.0 |
| INVOICE | 1.0 | 1.0 | 1.0 | 315.0 |
| ORDER | 0.998 | 1.0 | 0.999 | 595.0 |
| PAYMENT | 1.0 | 0.997 | 0.999 | 395.0 |
| REFUND | 1.0 | 1.0 | 1.0 | 510.0 |
| SHIPPING | 1.0 | 1.0 | 1.0 | 389.0 |
| SUBSCRIPTION | 1.0 | 1.0 | 1.0 | 245.0 |
| macro avg | 1.0 | 0.999 | 1.0 | 4751.0 |
| weighted avg | 1.0 | 1.0 | 1.0 | 4751.0 |

### Confusion matrix

| true \ pred | ACCOUNT | CANCEL | CONTACT | DELIVERY | FEEDBACK | INVOICE | ORDER | PAYMENT | REFUND | SHIPPING | SUBSCRIPTION |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ACCOUNT | 1010 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CANCEL | 0 | 185 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CONTACT | 0 | 0 | 387 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| DELIVERY | 0 | 0 | 0 | 322 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| FEEDBACK | 0 | 0 | 0 | 0 | 397 | 0 | 0 | 0 | 0 | 0 | 0 |
| INVOICE | 0 | 0 | 0 | 0 | 0 | 315 | 0 | 0 | 0 | 0 | 0 |
| ORDER | 0 | 0 | 0 | 0 | 0 | 0 | 595 | 0 | 0 | 0 | 0 |
| PAYMENT | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 394 | 0 | 0 | 0 |
| REFUND | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 510 | 0 | 0 |
| SHIPPING | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 389 | 0 |
| SUBSCRIPTION | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 245 |

### Does the score depend on near-copies?

If the score came from memorising near-copies, accuracy would drop on test rows that
are least similar to training. It does not drop much: the dataset is template-generated
and each category has very distinctive wording, so this test set is easy. The score on
hand-written messages (my_20.md) is the better guide to real-world performance.

| similarity to closest train row | test rows | accuracy |
|---|---|---|
| (0.0, 0.5] | 32 | 0.9688 |
| (0.5, 0.6] | 92 | 0.9891 |
| (0.6, 0.7] | 464 | 1.0 |
| (0.7, 0.8] | 2396 | 1.0 |
| (0.8, 0.9] | 1767 | 1.0 |

## 15 most confident wrong predictions

Read these for doubtful labels: sometimes the model is right and the label is not.

| instruction | category | intent | predicted | confidence |
|---|---|---|---|---|
| can i order frrom {{Delivery Country}} | DELIVERY | delivery_options | ORDER | 0.958 |
| I get an error when I try to check out | PAYMENT | payment_issue | DELIVERY | 0.346 |

## Wrong predictions explained

See the five explained errors in [my_20.md](my_20.md).
