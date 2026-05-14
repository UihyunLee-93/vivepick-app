import SwiftUI
import Foundation

// MARK: - Color Extensions
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet(charactersIn: "#"))
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)

        let r = Double((int >> 16) & 0xFF) / 255.0
        let g = Double((int >> 8) & 0xFF) / 255.0
        let b = Double(int & 0xFF) / 255.0
        self.init(red: r, green: g, blue: b)
    }
}

// MARK: - Market Model
enum MarketState: String, Codable {
    case strong = "강세"
    case watch = "관망"
    case caution = "주의"
    case recover = "회복"

    var icon: String {
        switch self {
        case .strong: return "flame.fill"
        case .watch: return "cloud.fill"
        case .caution: return "eye.fill"
        case .recover: return "sparkles"
        }
    }

    var color: Color {
        switch self {
        case .strong: return VPTheme.bullish
        case .watch: return VPTheme.neutral
        case .caution: return VPTheme.warning
        case .recover: return Color(red: 0.35, green: 0.82, blue: 0.72)
        }
    }
}

struct Vibe: Identifiable, Codable {
    let id: UUID
    let tag: String
    let title: String
    let state: MarketState
    let summary: String
    let detail: String
    let relatedStocks: [String]
    let trend: [Double]

    init(
        tag: String,
        title: String,
        state: MarketState,
        summary: String,
        detail: String,
        relatedStocks: [String],
        trend: [Double]
    ) {
        self.id = UUID()
        self.tag = tag
        self.title = title
        self.state = state
        self.summary = summary
        self.detail = detail
        self.relatedStocks = relatedStocks
        self.trend = trend
    }
}

struct SavedVibe: Identifiable, Codable {
    let id = UUID()
    let vibe: Vibe
    let savedDate: Date
    let memo: String

    init(vibe: Vibe, savedDate: Date = Date(), memo: String = "") {
        self.vibe = vibe
        self.savedDate = savedDate
        self.memo = memo
    }
}

struct UserProfile: Identifiable, Codable {
    let id = UUID()
    let name: String
    let email: String
    let avatar: String
    let interestTags: [String]
    let interestStocks: [String]
    let savedVibes: [SavedVibe]
    let isPro: Bool
}

// MARK: - Dummy Data
enum DummyData {
    static let vibes: [Vibe] = [
        Vibe(
            tag: "AI",
            title: "AI 강세",
            state: .strong,
            summary: "관심 확대 흐름",
            detail: "AI 인프라와 반도체 쪽으로 관심이 다시 모이는 흐름입니다.",
            relatedStocks: ["엔비디아", "SK하이닉스", "한미반도체"],
            trend: [34, 38, 45, 52, 58, 63, 70]
        ),
        Vibe(
            tag: "반도체",
            title: "반도체 강세",
            state: .strong,
            summary: "실적 기대 유지",
            detail: "메모리와 AI 반도체 관련 종목에 관심이 이어지는 분위기입니다.",
            relatedStocks: ["삼성전자", "SK하이닉스", "TSMC"],
            trend: [42, 44, 47, 51, 55, 59, 64]
        ),
        Vibe(
            tag: "2차전지",
            title: "2차전지 관망",
            state: .watch,
            summary: "거래량 둔화",
            detail: "단기 반등 이후 시장이 잠시 방향을 지켜보는 분위기입니다.",
            relatedStocks: ["LG에너지솔루션", "에코프로비엠"],
            trend: [55, 52, 48, 45, 43, 42, 40]
        ),
        Vibe(
            tag: "금리",
            title: "금리 변수",
            state: .caution,
            summary: "시장 관망 분위기",
            detail: "금리 발표를 앞두고 성장주 쪽 움직임이 조심스러운 상황입니다.",
            relatedStocks: ["나스닥", "미국 기술주"],
            trend: [44, 41, 43, 39, 42, 40, 38]
        ),
        Vibe(
            tag: "로봇",
            title: "로봇 회복",
            state: .recover,
            summary: "관심 회복 흐름",
            detail: "자동화와 로봇 관련 이슈가 다시 관심을 받는 흐름입니다.",
            relatedStocks: ["레인보우로보틱스", "두산로보틱스"],
            trend: [31, 35, 34, 38, 42, 46, 49]
        ),
        Vibe(
            tag: "미국기술주",
            title: "미국 기술주 강세",
            state: .strong,
            summary: "기술주 관심 유지",
            detail: "AI와 클라우드 중심으로 미국 기술주 관심이 이어지는 분위기입니다.",
            relatedStocks: ["엔비디아", "마이크로소프트", "AMD"],
            trend: [48, 50, 55, 57, 62, 66, 71]
        )
    ]

    static let userProfile = UserProfile(
        name: "김지원",
        email: "jiwon@vibepick.app",
        avatar: "지",
        interestTags: ["AI", "반도체", "로봇", "미국기술주"],
        interestStocks: ["엔비디아", "SK하이닉스", "삼성전자"],
        savedVibes: [
            SavedVibe(vibe: vibes[0], memo: "관심 확대 흐름"),
            SavedVibe(vibe: vibes[2], memo: "거래량 둔화"),
            SavedVibe(vibe: vibes[3], memo: "시장 관망 분위기")
        ],
        isPro: true
    )
}
