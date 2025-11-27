import express from "express";
import pool from "../db/db.js";

const router = express.Router();

// Aktivacija MAC-a
router.post("/activate", async (req, res) => {
    const { mac, plan } = req.body;

    if (!mac || !plan) return res.status(400).json({ error: "Missing data" });

    await pool.query(
        "INSERT INTO devices (mac, plan, created_at) VALUES (?, ?, NOW())",
        [mac, plan]
    );

    res.json({ success: true });
});

export default router;

