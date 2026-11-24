# Bitext dataset exploration

## 1. Overview

Rows: **26,872**

Columns: flags, instruction, category, intent, response

## 2. Labels

11 categories, 27 intents.

### Rows per category

| category | rows | share_% |
|---|---|---|
| ACCOUNT | 5986 | 22.3 |
| ORDER | 3988 | 14.8 |
| REFUND | 2992 | 11.1 |
| INVOICE | 1999 | 7.4 |
| CONTACT | 1999 | 7.4 |
| PAYMENT | 1998 | 7.4 |
| FEEDBACK | 1997 | 7.4 |
| DELIVERY | 1994 | 7.4 |
| SHIPPING | 1970 | 7.3 |
| SUBSCRIPTION | 999 | 3.7 |
| CANCEL | 950 | 3.5 |

### Rows per intent

| intent | rows |
|---|---|
| check_invoice | 1000 |
| complaint | 1000 |
| contact_customer_service | 1000 |
| edit_account | 1000 |
| switch_account | 1000 |
| check_payment_methods | 999 |
| contact_human_agent | 999 |
| delivery_period | 999 |
| get_invoice | 999 |
| newsletter_subscription | 999 |
| payment_issue | 999 |
| registration_problems | 999 |
| cancel_order | 998 |
| place_order | 998 |
| track_refund | 998 |
| change_order | 997 |
| check_refund_policy | 997 |
| create_account | 997 |
| get_refund | 997 |
| review | 997 |
| set_up_shipping_address | 997 |
| delete_account | 995 |
| delivery_options | 995 |
| recover_password | 995 |
| track_order | 995 |
| change_shipping_address | 973 |
| check_cancellation_fee | 950 |

### Intents in each category

| category | intents |
|---|---|
| ACCOUNT | create_account, delete_account, edit_account, recover_password, registration_problems, switch_account |
| CANCEL | check_cancellation_fee |
| CONTACT | contact_customer_service, contact_human_agent |
| DELIVERY | delivery_options, delivery_period |
| FEEDBACK | complaint, review |
| INVOICE | check_invoice, get_invoice |
| ORDER | cancel_order, change_order, place_order, track_order |
| PAYMENT | check_payment_methods, payment_issue |
| REFUND | check_refund_policy, get_refund, track_refund |
| SHIPPING | change_shipping_address, set_up_shipping_address |
| SUBSCRIPTION | newsletter_subscription |

Every intent belongs to exactly one category.

## 3. Message length (words)

min 1, median 9, max 16

| category | min | median | max |
|---|---|---|---|
| ACCOUNT | 1 | 8.0 | 16 |
| CANCEL | 2 | 8.0 | 15 |
| CONTACT | 1 | 9.0 | 15 |
| DELIVERY | 2 | 10.0 | 16 |
| FEEDBACK | 1 | 9.0 | 15 |
| INVOICE | 2 | 9.0 | 15 |
| ORDER | 1 | 8.0 | 16 |
| PAYMENT | 2 | 8.0 | 15 |
| REFUND | 2 | 10.0 | 16 |
| SHIPPING | 2 | 8.0 | 15 |
| SUBSCRIPTION | 3 | 8.0 | 15 |

## 4. Examples (3 per category, random_state=42)

### ACCOUNT

| intent | instruction |
|---|---|
| registration_problems | where to notify of problems with sign-up? |
| switch_account | wanna  use the {{Account Type}} profile help me |
| recover_password | I cannot retrieve the bloody PIN code of my profile |

### CANCEL

| intent | instruction |
|---|---|
| check_cancellation_fee | I am tring to see the early exit penalty |
| check_cancellation_fee | check cancellation fee |
| check_cancellation_fee | I do not know how to check the cancellation charge |

### CONTACT

| intent | instruction |
|---|---|
| contact_customer_service | I have to check what hours I can reach customer assistance |
| contact_customer_service | assistance to see what hours i can call customer service |
| contact_customer_service | what do I have to do to call customer service? |

### DELIVERY

| intent | instruction |
|---|---|
| delivery_options | do you shp to {{Delivery City}}? |
| delivery_period | help seeing how long it takes for my shipment to arrive |
| delivery_options | do ya ship to {{Delivery Country}} |

### FEEDBACK

| intent | instruction |
|---|---|
| complaint | how do I lodge a damn consumer reclamation? |
| complaint | how tolodge a customer complaint |
| complaint | I'm not happy with ur work how do i make a claim |

### INVOICE

| intent | instruction |
|---|---|
| check_invoice | I don't know what to do to locate the involice #85632 |
| check_invoice | i need assistance to give a quick look at the invoice #37777 |
| check_invoice | what do i have to do to give a quick look at my bill #00108 |

### ORDER

| intent | instruction |
|---|---|
| change_order | can you help me remove something from purchase {{Order Number}}? |
| place_order | i dont know how  to purchase several products |
| change_order | can uhelp me swappping a product of purchase {{Order Number}} |

### PAYMENT

| intent | instruction |
|---|---|
| check_payment_methods | help me see your allowed payment modalities |
| check_payment_methods | where to check what payment payment modalities are available |
| check_payment_methods | I need to check the available payment methods, help me |

### REFUND

| intent | instruction |
|---|---|
| check_refund_policy | I need to check in which cases can I ask for a reimbursement |
| track_refund | I am waiting for a reimbursement of {{Currency Symbol}}{{Refund Amount}} |
| get_refund | I don't know how I can get a restitution of my money |

### SHIPPING

| intent | instruction |
|---|---|
| change_shipping_address | I have issues editing my address |
| change_shipping_address | can you help me to correct my address? |
| set_up_shipping_address | ido not know how i can submit the new shipping address |

### SUBSCRIPTION

| intent | instruction |
|---|---|
| newsletter_subscription | i want assistance unsubscribing from the newsletter |
| newsletter_subscription | I need to unsubscribe from the newsletter, can yyou help me? |
| newsletter_subscription | can uhelp me subscribe to ur newsletter |

## 5. Duplicates

Exact duplicate instructions (extra copies): **2,237** (8.3%)

Duplicates after normalising (lowercase, no punctuation, {{...}} -> ENT): **3,140** (11.7%). Unique normalised texts: 23,732

### Most repeated normalised texts

| normalised instruction | times |
|---|---|
| is it possible to order from ENT | 36 |
| is it possible to place an order from ENT | 35 |
| can i place an order from ENT | 28 |
| can i order from ENT | 28 |
| do you deliver to ENT | 22 |
| do you ship to ENT | 20 |
| shipments to ENT | 14 |
| do ya deliver to ENT | 14 |
| shipping to ENT | 13 |
| deliveries to ENT | 13 |

## 6. Same text, different category

Normalised texts with more than one category: **0**, covering **0** rows.


## 7. Placeholders

Rows containing a {{...}} placeholder: **6,670** (24.8%)

| placeholder | count |
|---|---|
| {{Order Number}} | 2907 |
| {{Account Type}} | 1011 |
| {{Person Name}} | 887 |
| {{Account Category}} | 822 |
| {{Refund Amount}} | 624 |
| {{Currency Symbol}} | 372 |
| {{Delivery City}} | 234 |
| {{Delivery Country}} | 177 |
| {{Invoice Number}} | 8 |

## 8. Flags

394 distinct flag combinations. Top 20:

| flags | rows |
|---|---|
| BL | 5212 |
| BLQ | 2467 |
| BIL | 2138 |
| BLM | 1297 |
| BILQ | 1057 |
| BLQZ | 970 |
| BLZ | 902 |
| BKL | 862 |
| BLMQ | 600 |
| BEL | 533 |
| BILM | 521 |
| BCL | 484 |
| BCIL | 427 |
| BILQZ | 412 |
| BILP | 363 |
| B | 353 |
| BK | 352 |
| BQ | 340 |
| BKLZ | 322 |
| BLW | 309 |

Flag letters per the dataset card: B basic syntax, I interrogative, C coordinated, N negation, M morphological variation, L semantic variation (synonyms), P politeness, Q colloquial, W offensive, K keyword mode, E abbreviations, Z errors and typos.

## 9. Shortcut clues (placeholders and digits)

If a token only ever appears with one category, a model can learn the token instead of the meaning. Real customers never type {{...}}.

| placeholder | rows | top_category | share_in_top |
|---|---|---|---|
| {{Order Number}} | 2907 | ORDER | 1.0 |
| {{Account Type}} | 1011 | ACCOUNT | 1.0 |
| {{Person Name}} | 887 | INVOICE | 1.0 |
| {{Account Category}} | 822 | ACCOUNT | 1.0 |
| {{Refund Amount}} | 624 | REFUND | 1.0 |
| {{Currency Symbol}} | 372 | REFUND | 1.0 |
| {{Delivery City}} | 234 | DELIVERY | 1.0 |
| {{Delivery Country}} | 177 | DELIVERY | 1.0 |
| {{Invoice Number}} | 8 | INVOICE | 1.0 |

### Rows containing digits

| category | rows_with_digits |
|---|---|
| INVOICE | 1045 |
| ORDER | 37 |
| REFUND | 7 |
