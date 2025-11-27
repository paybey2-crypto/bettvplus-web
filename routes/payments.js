import express from "express";
import Stripe from "stripe";
import pool from "../db/db.js";

const router = express.Router();
const stripe = new Stripe(process.env.STRIPE_SECRET);

// Stripe webhook
router.post("/webhook", express.raw({ type: 'application/json' }), async (req, res) => {
    let event;

    try {
        event = stripe.webhooks.constructEvent(
            req.body,
            req.headers["stripe-signature"],
            process.env.STRIPE_WEBHOOK_SECRET
        );
    } catch (err) {
        return res.status(400).send(`Webhook error: ${err.message}`);
    }

    if (event.type === "checkout.session.completed") {
        const session = event.data.object;

        const mac = session.client_reference_id;
        const plan = session.metadata?.plan ?? "year";

        await pool.query(
            "INSERT INTO devices (mac, plan, created_at) VALUES (?, ?, NOW())",
            [mac, plan]
        );
    }

    res.json({ received: true });
});

export default router;

