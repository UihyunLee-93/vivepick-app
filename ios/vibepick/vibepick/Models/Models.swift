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

// MARK: - Brief Topic
struct BriefTopic: Identifiable, Codable {
    let id: UUID
    let topicNumber: Int
    let category: BriefCategory
    let subCategory: String
    let title: String
    let summary: String
    let mood: BriefMood
    let keyPoints: [String]
    let relatedStocks: [String]
    let detail: String

    var categoryLabel: String {
        category.rawValue
    }

    init(
        topicNumber: Int,
        category: BriefCategory,
        subCategory: String,
        title: String,
        summary: String,
        mood: BriefMood,
        keyPoints: [String],
        relatedStocks: [String],
        detail: String
    ) {
        self.id = UUID()
        self.topicNumber = topicNumber
        self.category = category
        self.subCategory = subCategory
        self.title = title
        self.summary = summary
        self.mood = mood
        self.keyPoints = keyPoints
        self.relatedStocks = relatedStocks
        self.detail = detail
    }
}

// MARK: - Brief
struct Brief: Identifiable, Codable {
    let id: UUID
    let slot: BriefSlot
    let isUnlocked: Bool
    let topics: [BriefTopic]

    init(slot: BriefSlot, isUnlocked: Bool, topics: [BriefTopic]) {
        self.id = UUID()
        self.slot = slot
        self.isUnlocked = isUnlocked
        self.topics = topics
    }
}

// MARK: - Dummy Data
enum DummyData {
    static let morningTopics = makeTopics(for: .morning)
    static let noonTopics = makeTopics(for: .noon)
    static let nightTopics = makeTopics(for: .night)

    static func makeBriefs(isProMode: Bool) -> [Brief] {
        [
            Brief(slot: .morning, isUnlocked: true, topics: morningTopics),
            Brief(slot: .noon, isUnlocked: isProMode, topics: noonTopics),
            Brief(slot: .night, isUnlocked: isProMode, topics: nightTopics)
        ]
    }

    static let briefs = makeBriefs(isProMode: false)

    private static func makeTopics(for slot: BriefSlot) -> [BriefTopic] {
        topicSeeds.enumerated().map { index, seed in
            BriefTopic(
                topicNumber: index + 1,
                category: seed.category,
                subCategory: seed.subCategory,
                title: title(for: slot, seed: seed),
                summary: summary(for: slot, seed: seed),
                mood: mood(for: slot, index: index),
                keyPoints: keyPoints(for: slot, seed: seed),
                relatedStocks: seed.relatedStocks,
                detail: detail(for: slot, seed: seed)
            )
        }
    }

    private static func title(for slot: BriefSlot, seed: TopicSeed) -> String {
        switch slot {
        case .morning: return "\(seed.label) 장전 체크포인트 부각"
        case .noon: return "\(seed.label) 장중 수급 변화 감지"
        case .night: return "\(seed.label) 마감 흐름과 내일 변수"
        }
    }

    private static func summary(for slot: BriefSlot, seed: TopicSeed) -> String {
        switch slot {
        case .morning: return "개장 전 \(seed.label) 관련 이슈와 선반영 가능성을 점검합니다."
        case .noon: return "오전 거래 이후 \(seed.label) 종목군의 강약과 뉴스 반응을 정리합니다."
        case .night: return "마감 후 \(seed.label) 흐름을 복기하고 다음 거래일 관전 포인트를 정리합니다."
        }
    }

    private static func keyPoints(for slot: BriefSlot, seed: TopicSeed) -> [String] {
        switch slot {
        case .morning:
            return [
                "해외 뉴스와 선물 흐름이 \(seed.label) 심리에 영향",
                "개장 초반 대형주 수급 확인 필요",
                "관련 테마 확산 여부가 단기 방향성 결정"
            ]
        case .noon:
            return [
                "오전 강세 종목과 약세 종목 간 차별화 확대",
                "기관·외국인 수급 변화가 \(seed.label) 흐름을 좌우",
                "오후 변동성 구간에서 거래대금 유지 여부 체크"
            ]
        case .night:
            return [
                "마감 가격 기준으로 단기 추세 유지 여부 확인",
                "시간외 뉴스와 해외 지표가 다음날 출발점에 영향",
                "\(seed.label) 내 주도 종목 교체 가능성 점검"
            ]
        }
    }

    private static func detail(for slot: BriefSlot, seed: TopicSeed) -> String {
        switch slot {
        case .morning:
            return "오늘 \(seed.label) 영역은 장 시작 전부터 관련 뉴스와 매크로 변수의 영향을 받고 있습니다. 초반에는 기대감이 먼저 반영될 수 있지만, 실제 수급이 이어지는지 확인하는 것이 중요합니다."
        case .noon:
            return "오전장을 지나며 \(seed.label) 관련 종목은 뉴스 반응과 거래대금에 따라 흐름이 갈리고 있습니다. 오후에는 지수 방향보다 개별 이슈의 지속력이 더 중요한 체크포인트입니다."
        case .night:
            return "마감 기준 \(seed.label) 흐름은 단기 모멘텀과 차익실현 압력이 함께 나타났습니다. 내일은 해외 시장 반응과 장전 뉴스가 재평가의 핵심 변수가 될 가능성이 큽니다."
        }
    }

    private static func mood(for slot: BriefSlot, index: Int) -> BriefMood {
        switch (slot, index % 3) {
        case (.morning, 0), (.noon, 1), (.night, 2): return .positive
        case (.morning, 1), (.noon, 2), (.night, 0): return .neutral
        default: return .negative
        }
    }

    private struct TopicSeed {
        let category: BriefCategory
        let subCategory: String
        let label: String
        let relatedStocks: [String]
    }

    private static let topicSeeds: [TopicSeed] = [
        TopicSeed(category: .aiTech, subCategory: "AI", label: "AI · 기술", relatedStocks: ["엔비디아", "SK하이닉스", "삼성전자", "한미반도체"]),
        TopicSeed(category: .finance, subCategory: "금리", label: "금융", relatedStocks: ["KB금융", "신한지주", "하나금융", "카카오뱅크"]),
        TopicSeed(category: .energy, subCategory: "원유", label: "에너지", relatedStocks: ["S-Oil", "SK이노베이션", "한국전력", "두산에너빌리티"]),
        TopicSeed(category: .mobility, subCategory: "전기차", label: "모빌리티", relatedStocks: ["현대차", "기아", "LG에너지솔루션", "포스코퓨처엠"]),
        TopicSeed(category: .bio, subCategory: "신약", label: "바이오", relatedStocks: ["삼성바이오로직스", "셀트리온", "유한양행", "리가켐바이오"]),
        TopicSeed(category: .consumerLife, subCategory: "소비", label: "소비 · 라이프", relatedStocks: ["아모레퍼시픽", "호텔신라", "CJ제일제당", "BGF리테일"]),
        TopicSeed(category: .industryManufacturing, subCategory: "제조", label: "산업 · 제조", relatedStocks: ["HD현대중공업", "두산밥캣", "LS", "한화오션"]),
        TopicSeed(category: .global, subCategory: "미국", label: "글로벌", relatedStocks: ["S&P500", "나스닥", "애플", "마이크로소프트"]),
        TopicSeed(category: .crypto, subCategory: "디지털자산", label: "크립토", relatedStocks: ["비트코인", "이더리움", "코인베이스", "두나무"]),
        TopicSeed(category: .contentEntertainment, subCategory: "콘텐츠", label: "콘텐츠 · 엔터", relatedStocks: ["하이브", "JYP Ent.", "에스엠", "스튜디오드래곤"])
    ]
}
