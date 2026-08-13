# Ah Huat Nasi Lemak — Online Ordering System

## Requirements

- WHEN a customer opens the ordering page, THE System SHALL display all menu items within 2 seconds.
- THE System SHALL display each menu item with its name, price in SGD, and a photo.
- WHEN a customer adds an item to the cart, THE System SHALL update the displayed cart total within 500 milliseconds.
- WHEN a customer proceeds to checkout, THE System SHALL generate a PayNow QR code for the order total.
- WHEN the payment gateway confirms payment, THE System SHALL send an SMS order confirmation to the customer within 30 seconds.
- WHEN an item quantity reaches zero, THE System SHALL mark that item as out-of-stock on the menu page.
- IF an item becomes unavailable after a customer adds the item to the cart, THEN THE System SHALL notify the customer within 5 seconds and remove the item from the cart.
- THE System SHALL display pickup time slots in 15-minute intervals during stall operating hours.
- WHEN a customer selects delivery, THE System SHALL accept the order only IF the delivery address is within a 3 km radius of the stall.
- WHEN the payment gateway confirms a delivery order, THE System SHALL assign the order to an available driver within 60 seconds.
- WHEN the payment gateway confirms payment, THE System SHALL send the order confirmation message in English and in the customer-selected secondary language.
- THE System SHALL render all pages with minimum 16px font size and a maximum of 3 navigation steps from menu to checkout.
- WHEN an admin updates the menu, THE System SHALL save the changes and reflect them on the customer-facing menu within 5 seconds.
- WHILE concurrent orders exceed 50 per hour, THE System SHALL process each new order within 10 seconds of submission.
- IF an order remains unpaid for more than 10 minutes, THEN THE System SHALL cancel that order and release reserved stock.
- WHEN an order status changes, THE System SHALL send an SMS notification to the customer within 15 seconds.
- IF the payment gateway is unreachable for more than 5 seconds, THEN THE System SHALL display a retry prompt to the customer and log the failure.
- THE System SHALL schedule each pickup order into the nearest available 15-minute slot with no more than 5 orders per slot.
- WHEN a customer enters a postal code, THE System SHALL determine delivery eligibility by calculating the distance from the stall and accepting only addresses within 3 km.
- THE System SHALL display a real-time order tracker showing the current order status on the customer order page.
- WHEN an admin initiates a refund, THE System SHALL process the refund and update the order status to refunded within 30 seconds.
- WHEN an admin initiates a cancellation, THE System SHALL cancel the order and restore reserved stock within 10 seconds.
- WHEN an admin sets a daily special, THE System SHALL display that item in the first position of the menu page.
- THE System SHALL serve all pages with a p95 response time under 500 milliseconds for up to 200 concurrent users.
- WHEN a customer selects pickup, THE System SHALL send an SMS notification with the collection time within 30 seconds of order confirmation.
- IF a customer places an order outside operating hours, THEN THE System SHALL queue that order and process the order at the start of the next operating day.

## Interface Notes

- Payment integration uses the PayNow QR standard.
- Delivery routing is resolved server-side and dispatched to the driver pool.
- The customer-facing order tracker is rendered in the web client.

## Test Data

- Nasi Lemak Set A — $4.50
- Mee Siam — $4.00
- Teh Tarik — $1.80
- Otah Add-on — $1.00
- Nasi Lemak Set B (with Fried Chicken Wing) — $6.00
