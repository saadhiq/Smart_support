# Cleaning and leak-free split

## Cleaning (text compared after app.text.normalise)

| step | rows |
|---|---|
| loaded | 26,872 |
| dropped: same text with more than one category (0 texts) | 0 |
| dropped: exact duplicates after normalise | 3,348 |
| kept | 23,524 |

## Near-duplicate groups

Character 3-5-gram TF-IDF on the normalised text. Two texts are linked when cosine
similarity >= 0.85. Linked texts form one group (connected components).

- Groups: **7,885** for 23,524 rows
- Single-row groups: 6,108
- Largest group: 292 rows (1.2% of all rows)
- Groups containing more than one category: **8** (379 rows)

### 10 largest groups

| group_id | rows | categories | example |
|---|---|---|---|
| 4815 | 292 | SUBSCRIPTION | i try tro subscribe to the newsletter |
| 4812 | 245 | SUBSCRIPTION | how can i cancel the subscription to the company newsletter |
| 1252 | 186 | INVOICE | i have to see my invoice from ENT help me |
| 1536 | 182 | PAYMENT | i have got to list the allowed payment modalities help me |
| 7069 | 164 | SHIPPING | help to submit a fucking secondary delivery address |
| 7519 | 132 | ORDER | i cannot see purchase ENT current status |
| 7521 | 130 | ORDER | order ENT status |
| 1791 | 122 | REFUND | can i check in what cases can i ask to be reimbursed |
| 1792 | 120 | REFUND | could you show me in what situations can i ask for refunds |
| 5009 | 120 | PAYMENT | i need assistance notifying of a trouble with online payment |

### Near-identical texts with different categories (possible doubtful labels)

| group_id | category | norm |
|---|---|---|
| 548 | ORDER | i want information about correcting order ENT |
| 548 | SHIPPING | i need information about correcting my shipping address |
| 1416 | INVOICE | i awnt assistance to locate the bill ENT |
| 1416 | ORDER | i awnt assistance to locate order ENT |
| 1534 | PAYMENT | could you help me check what payment options are available |
| 1534 | DELIVERY | where do i check what damn shipment options are available |
| 1560 | PAYMENT | i need to see what payment methods are available help me |
| 1560 | DELIVERY | i try to check what shipping methods are available |
| 3639 | DELIVERY | i want to check when will my purchase arrive |
| 3639 | ORDER | when will purchase ENT arrive |
| 5012 | PAYMENT | need help informing of a problem with online payments |
| 5012 | ACCOUNT | i dont know how i can inform of an problem with sign up |
| 5028 | PAYMENT | i want assistance informing of a payment issue |
| 5028 | ACCOUNT | informing of issue with sign up |
| 5051 | PAYMENT | need assistance reporting a problem with payment |

### Choosing the threshold

A lower threshold makes groups bigger, so the test set is less similar to train
(stricter). Too low, and groups chain together into huge mixed groups and the
category balance breaks.

| threshold | groups | largest group | test share | max category gap | test sim >= 0.8 |
|---|---|---|---|---|---|
| 0.9 | 12,520 | 149 (0.6%) | 20.0% | 0.0 pts | 73.2% |
| 0.85 (used) | 7,885 | 292 (1.2%) | 20.2% | 1.2 pts | 37.2% |
| 0.8 | 4,643 | 1,505 (6.4%) | 17.6% | 7.8 pts | 0.0% |

## Split

StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42); the first
fold is the test set. Whole groups go to one side; category shares are kept similar.
Train 18,773 rows, test 4,751 rows (20.2%).
No group_id appears in both: True.

| category | train | test | train_% | test_% |
|---|---|---|---|---|
| ACCOUNT | 4039 | 1010 | 21.5 | 21.3 |
| CANCEL | 742 | 185 | 4.0 | 3.9 |
| CONTACT | 1551 | 387 | 8.3 | 8.1 |
| DELIVERY | 1295 | 323 | 6.9 | 6.8 |
| FEEDBACK | 1590 | 397 | 8.5 | 8.4 |
| INVOICE | 1262 | 315 | 6.7 | 6.6 |
| ORDER | 2382 | 595 | 12.7 | 12.5 |
| PAYMENT | 1581 | 395 | 8.4 | 8.3 |
| REFUND | 2039 | 510 | 10.9 | 10.7 |
| SHIPPING | 1557 | 389 | 8.3 | 8.2 |
| SUBSCRIPTION | 735 | 245 | 3.9 | 5.2 |

## Leak check

For every test row: cosine similarity to its closest training row (same character
TF-IDF). The random split is shown only for comparison; it is not used.

| split | test rows | sim >= 0.9 | sim >= 0.8 | median sim |
|---|---|---|---|---|
| grouped (used) | 4,751 | 0.0% | 37.2% | 0.78 |
| random (comparison only) | 4,705 | 54.5% | 81.4% | 0.91 |
