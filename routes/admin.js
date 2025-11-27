import express from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import pool from "../db/db.js";
import { auth } from "../utils/auth.js";

const router = express.Router();

// Admin login
router.post("/login", async (req, res) => {
    const { username, password } = req.body;

    const [rows] = await pool.query(
        "SELECT * FROM admins WHERE username = ? LIMIT 1",
        [username]
    );

    if (rows.length === 0) return res.status(401).json({ error: "User not found" });

    const admin = rows[0];

    const valid = await bcrypt.compare(password, admin.password);
    if (!valid) return res.status(401).json({ error: "Wrong password" });

    const token = jwt.sign({ id: admin.id }, process.env.JWT_SECRET, { expiresIn: "12h" });

    res.json({ token });
});

// Get all devices
router.get("/devices", auth, async (req, res) => {
    const [rows] = await pool.query("SELECT * FROM devices ORDER BY created_at DESC");
    res.json(rows);
});

// Delete device
router.delete("/device/:id", auth, async (req, res) => {
    await pool.query("DELETE FROM devices WHERE id = ?", [req.params.id]);
    res.json({ success: true });
});

export default router;

