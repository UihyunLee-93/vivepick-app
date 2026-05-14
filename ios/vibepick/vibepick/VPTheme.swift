import SwiftUI

enum VPTheme {
    static let background = Color(red: 0.07, green: 0.08, blue: 0.13)
    static let card = Color.white.opacity(0.05)
    static let cardSoft = Color.white.opacity(0.04)
    static let line = Color.white.opacity(0.08)

    static let orange = Color(red: 1.0, green: 0.52, blue: 0.32)
    static let accent = orange

    static let blue = Color(red: 0.42, green: 0.56, blue: 1.0)
    static let purple = Color(red: 0.58, green: 0.45, blue: 1.0)

    static let bullish = orange
    static let neutral = blue
    static let warning = purple

    static let grayText = Color.white.opacity(0.55)
    static let textPrimary = Color.white
    static let textSecondary = Color.white.opacity(0.65)
    static let textTertiary = Color.white.opacity(0.4)
}
