import SwiftUI

enum VPTheme {
    // Base palette — dark navy
    static let background       = Color(hex: "0B0C18")
    static let surface          = Color(hex: "151728")
    static let surfaceElevated  = Color(hex: "1E2138")

    static let card     = Color.white.opacity(0.05)
    static let cardSoft = Color.white.opacity(0.03)
    static let line     = Color.white.opacity(0.08)

    // Brand accent — purple → pink
    static let purple   = Color(hex: "8B5CF6")
    static let pink     = Color(hex: "EC4899")
    static let accent   = purple

    static let proGold  = Color(hex: "FBBF24")

    // Status
    static let positive = Color(hex: "34D399")
    static let neutral  = Color(hex: "60A5FA")
    static let negative = Color(hex: "F87171")

    // Category
    static let ai      = Color(hex: "A78BFA")
    static let finance = Color(hex: "34D399")
    static let energy  = Color(hex: "FB923C")

    // Text
    static let textPrimary   = Color.white
    static let textSecondary = Color.white.opacity(0.7)
    static let textTertiary  = Color.white.opacity(0.45)
    static let textMuted     = Color.white.opacity(0.3)
    static let grayText      = Color.white.opacity(0.55)

    // Legacy aliases (kept for splash/legacy refs)
    static let orange  = Color(hex: "FB923C")
    static let blue    = neutral
    static let bullish = positive
    static let warning = pink
}
