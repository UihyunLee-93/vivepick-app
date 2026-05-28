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

// MARK: - Temporary App Mode
struct AppMode {
    static let isProModeStorageKey = "isProModeEnabled"
    static let regularCategoryLimit = 3
}

struct NotificationPreferenceKey {
    static let morning = "morningNotificationEnabled"
    static let noon = "noonNotificationEnabled"
    static let night = "nightNotificationEnabled"
}

// MARK: - Brief Slot
enum BriefSlot: String, Codable, CaseIterable, Identifiable {
    case morning
    case noon
    case night

    var id: String { rawValue }

    var title: String {
        switch self {
        case .morning: return "아침 브리핑"
        case .noon:    return "점심 브리핑"
        case .night:   return "저녁 브리핑"
        }
    }

    var time: String {
        switch self {
        case .morning: return "07:30"
        case .noon:    return "12:30"
        case .night:   return "20:00"
        }
    }

    var emoji: String {
        switch self {
        case .morning: return "🌅"
        case .noon:    return "☀️"
        case .night:   return "🌙"
        }
    }

    var tagline: String {
        switch self {
        case .morning: return "장 시작 전 분위기 한눈에"
        case .noon:    return "오후 흐름 정리 + 변동 체크"
        case .night:   return "마감 정리 · 내일 전망"
        }
    }

    var gradientColors: [Color] {
        switch self {
        case .morning:
            return [Color(hex: "FF8A4C"), Color(hex: "FF3E7F"), Color(hex: "8B5CF6")]
        case .noon:
            return [Color(hex: "FFB86B"), Color(hex: "5BA8FF"), Color(hex: "8B5CF6")]
        case .night:
            return [Color(hex: "1F1B5C"), Color(hex: "6E4FF2"), Color(hex: "0B0C18")]
        }
    }

    var backdropColors: [Color] {
        switch self {
        case .morning:
            return [Color(hex: "FF8A4C").opacity(0.34), Color(hex: "EC4899").opacity(0.16), .clear]
        case .noon:
            return [Color(hex: "5BA8FF").opacity(0.30), Color(hex: "FFE7A1").opacity(0.14), .clear]
        case .night:
            return [Color(hex: "6E4FF2").opacity(0.34), Color(hex: "1F1B5C").opacity(0.22), .clear]
        }
    }

    var fullBackdropColors: [Color] {
        switch self {
        case .morning:
            return [Color(hex: "2A1224"), Color(hex: "17101F"), VPTheme.background]
        case .noon:
            return [Color(hex: "102035"), Color(hex: "121526"), VPTheme.background]
        case .night:
            return [Color(hex: "14113A"), Color(hex: "101126"), VPTheme.background]
        }
    }

    var backdropSymbol: String {
        switch self {
        case .morning: return "sunrise.fill"
        case .noon: return "sun.max.fill"
        case .night: return "moon.stars.fill"
        }
    }
}

// MARK: - Brief Category
enum BriefCategory: String, Codable, CaseIterable, Identifiable {
    case all = "전체"
    case aiTech = "AI · 기술"
    case finance = "금융"
    case energy = "에너지"
    case mobility = "모빌리티"
    case bio = "바이오"
    case consumerLife = "소비 · 라이프"
    case industryManufacturing = "산업 · 제조"
    case global = "글로벌"
    case crypto = "크립토"
    case contentEntertainment = "콘텐츠 · 엔터"

    static let selectedCategoriesStorageKey = "selectedBriefCategoryIDs"
    static let selectableCategories = allCases.filter { $0 != .all }
    static let defaultSelectedCategoryIDs = selectableCategories.map(\.rawValue).joined(separator: ",")

    var id: String { rawValue }

    static func categories(from storedValue: String, limit: Int? = nil) -> Set<BriefCategory> {
        let values = storedValue
            .split(separator: ",")
            .compactMap { BriefCategory(rawValue: String($0)) }
            .filter { $0 != .all }

        let categories = values.isEmpty ? selectableCategories : values
        if let limit {
            return Set(categories.prefix(limit))
        }

        return Set(categories)
    }

    static func storageValue(for categories: Set<BriefCategory>, limit: Int? = nil) -> String {
        let orderedCategories = selectableCategories.filter { categories.contains($0) }
        let limitedCategories = limit.map { Array(orderedCategories.prefix($0)) } ?? orderedCategories
        return limitedCategories.map(\.rawValue).joined(separator: ",")
    }

    var iconName: String {
        switch self {
        case .all: return "square.grid.2x2.fill"
        case .aiTech: return "cpu.fill"
        case .finance: return "chart.line.uptrend.xyaxis"
        case .energy: return "bolt.fill"
        case .mobility: return "car.fill"
        case .bio: return "cross.case.fill"
        case .consumerLife: return "bag.fill"
        case .industryManufacturing: return "gearshape.2.fill"
        case .global: return "globe.americas.fill"
        case .crypto: return "bitcoinsign.circle.fill"
        case .contentEntertainment: return "play.rectangle.fill"
        }
    }

    var color: Color {
        switch self {
        case .all: return Color(hex: "8B5CF6")
        case .aiTech: return Color(hex: "A78BFA")
        case .finance: return Color(hex: "34D399")
        case .energy: return Color(hex: "FB923C")
        case .mobility: return Color(hex: "38BDF8")
        case .bio: return Color(hex: "22C55E")
        case .consumerLife: return Color(hex: "F472B6")
        case .industryManufacturing: return Color(hex: "94A3B8")
        case .global: return Color(hex: "60A5FA")
        case .crypto: return Color(hex: "FBBF24")
        case .contentEntertainment: return Color(hex: "F97316")
        }
    }
}

// MARK: - Brief Mood
enum BriefMood: String, Codable {
    case positive = "긍정적"
    case neutral  = "중립"
    case negative = "부정적"

    var arrow: String {
        switch self {
        case .positive: return "↗"
        case .neutral:  return "→"
        case .negative: return "↘"
        }
    }

    var color: Color {
        switch self {
        case .positive: return Color(hex: "34D399")
        case .neutral:  return Color(hex: "60A5FA")
        case .negative: return Color(hex: "F87171")
        }
    }
}

// MARK: - Brief (서버 응답과 1:1)
struct Brief: Identifiable, Codable {
    let id: Int
    let title: String
    let summary: String
    let positivePoints: [String]
    let negativePoints: [String]
    let relatedStocks: [String]
    let relatedSectors: [String]
    let publishedAt: Date

    enum CodingKeys: String, CodingKey {
        case id, title, summary
        case positivePoints = "positive_points"
        case negativePoints = "negative_points"
        case relatedStocks = "related_stocks"
        case relatedSectors = "related_sectors"
        case publishedAt = "published_at"
    }

    /// publishedAt의 시(時)를 기준으로 슬롯 분류
    var slot: BriefSlot {
        let hour = Calendar.current.component(.hour, from: publishedAt)
        switch hour {
        case 0..<11: return .morning
        case 11..<17: return .noon
        default: return .night
        }
    }

    var categories: [BriefCategory] {
        relatedSectors.compactMap { BriefCategory(rawValue: $0) }
    }

    var primaryCategory: BriefCategory {
        categories.first ?? .all
    }

    var categoryLabel: String {
        primaryCategory.rawValue
    }

    /// 긍정/부정 포인트 수 비교로 무드 추론
    var mood: BriefMood {
        if positivePoints.count > negativePoints.count {
            return .positive
        } else if negativePoints.count > positivePoints.count {
            return .negative
        }
        return .neutral
    }
}

// MARK: - Brief Slot Group (Home 화면 슬롯 단위 묶음)
struct BriefSlotGroup: Identifiable {
    let slot: BriefSlot
    let briefs: [Brief]
    let isUnlocked: Bool

    var id: String { slot.id }
    var count: Int { briefs.count }

    static func makeGroups(from briefs: [Brief], isProMode: Bool) -> [BriefSlotGroup] {
        let sorted = briefs.sorted { $0.publishedAt > $1.publishedAt }
        let grouped = Dictionary(grouping: sorted, by: { $0.slot })
        return BriefSlot.allCases.map { slot in
            BriefSlotGroup(
                slot: slot,
                briefs: grouped[slot] ?? [],
                isUnlocked: slot == .morning || isProMode
            )
        }
    }
}

// MARK: - Dummy Data (Preview 전용)
enum DummyData {
    static let briefs: [Brief] = makeSampleBriefs()

    static func slotGroups(isProMode: Bool = true) -> [BriefSlotGroup] {
        BriefSlotGroup.makeGroups(from: briefs, isProMode: isProMode)
    }

    private static func makeSampleBriefs() -> [Brief] {
        let cal = Calendar.current
        let today = Date()
        let morning = cal.date(bySettingHour: 8, minute: 0, second: 0, of: today) ?? today
        let noon = cal.date(bySettingHour: 13, minute: 0, second: 0, of: today) ?? today
        let night = cal.date(bySettingHour: 21, minute: 0, second: 0, of: today) ?? today

        return [
            Brief(
                id: 1,
                title: "AI 반도체 수요 회복 신호 감지",
                summary: "엔비디아·SK하이닉스 등 AI 메모리 공급망 전반에서 주문 증가가 확인되고 있습니다.",
                positivePoints: ["주요 클라우드 사업자 발주 재개", "HBM 가격 안정세"],
                negativePoints: ["일부 구간 재고 부담 잔존"],
                relatedStocks: ["엔비디아", "SK하이닉스", "삼성전자"],
                relatedSectors: ["AI · 기술"],
                publishedAt: morning
            ),
            Brief(
                id: 2,
                title: "금융주, 금리 동결 기대에 강세",
                summary: "중앙은행 금리 동결 가능성이 확대되며 은행주가 동반 반등했습니다.",
                positivePoints: ["순이자마진 개선 기대", "배당주 관심 증가"],
                negativePoints: ["대출 성장 둔화 우려"],
                relatedStocks: ["KB금융", "신한지주", "하나금융"],
                relatedSectors: ["금융"],
                publishedAt: noon
            ),
            Brief(
                id: 3,
                title: "야간 글로벌 시장, 변동성 확대",
                summary: "중동 지정학 이슈로 유가와 안전자산 흐름이 엇갈리고 있습니다.",
                positivePoints: ["에너지 섹터 단기 모멘텀"],
                negativePoints: ["증시 위험회피 심리 확대", "환율 변동성"],
                relatedStocks: ["S-Oil", "SK이노베이션"],
                relatedSectors: ["에너지", "글로벌"],
                publishedAt: night
            )
        ]
    }
}
