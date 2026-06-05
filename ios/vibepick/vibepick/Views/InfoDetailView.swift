import SwiftUI

// MARK: - Info Page Definitions
enum InfoPage: String, Identifiable, Hashable {
    case appInfo
    case help
    case terms

    var id: String { rawValue }

    var title: String {
        switch self {
        case .appInfo: return "앱 정보 · 투자 유의사항"
        case .help:    return "도움말"
        case .terms:   return "이용약관 · 개인정보"
        }
    }

    var sections: [InfoSection] {
        switch self {
        case .appInfo:
            return [
                InfoSection(
                    title: "VibePick",
                    body: "VibePick은 하루 3번(아침·점심·저녁) 시장 분위기를 한눈에 정리해주는 AI 브리핑 서비스입니다.\n\n버전 1.0.0 · 빌드 2026.05"
                ),
                InfoSection(
                    title: "투자 유의사항",
                    body: "VibePick에서 제공하는 모든 정보는 시장 흐름 참고용이며 투자 권유나 매매 추천이 아닙니다.\n\n모든 투자에는 손실 가능성이 있으며, 최종 투자 판단과 책임은 이용자 본인에게 있습니다. 종목 정보·가격·뉴스는 외부 데이터를 기반으로 제공되며, 실시간성·정확성을 100% 보장하지 않습니다."
                ),
                InfoSection(
                    title: "AI 콘텐츠 생성",
                    body: "브리핑 본문과 요약은 AI 모델이 다수 출처를 종합해 자동 생성합니다. 사실 관계가 틀리거나 표현이 어색할 수 있으며, 중요한 결정 전에는 원문과 1차 자료를 직접 확인해 주세요."
                )
            ]

        case .help:
            return [
                InfoSection(
                    title: "아침 · 점심 · 저녁 브리핑",
                    body: "하루 3번 시장 흐름을 정리해 푸시로 보내드립니다.\n• 아침 브리핑 08:00 — 장 시작 전 분위기\n• 점심 브리핑 12:30 — 오후 흐름 점검\n• 저녁 브리핑 20:00 — 마감 정리와 내일 전망"
                ),
                InfoSection(
                    title: "카드 상세 화면",
                    body: "브리핑 카드를 누르면 현재 분위기, 핵심 요약, 주요 포인트, 관련 종목까지 한 페이지로 정리되어 있습니다. 카테고리 탭(AI · 금융 · 에너지)으로 관심 분야만 골라볼 수도 있어요."
                ),
                InfoSection(
                    title: "문의",
                    body: "버그 제보나 기능 요청은 https://vibepick.github.io 에서 확인해 주세요."
                )
            ]

        case .terms:
            return [
                InfoSection(
                    title: "이용약관 (요약)",
                    body: "VibePick은 회원에게 시장 분위기 브리핑 서비스를 제공합니다. 회원은 본 서비스를 합법적인 개인 정보 열람 목적으로만 이용해야 하며, 콘텐츠를 무단 복제·재배포·상업적 활용할 수 없습니다.\n\n지원 페이지는 https://vibepick.github.io 에서 확인할 수 있습니다."
                ),
                InfoSection(
                    title: "개인정보 처리방침 (요약)",
                    body: "VibePick은 서비스 제공을 위해 최소한의 정보(계정 식별자, 푸시 토큰)를 수집합니다. 수집된 정보는 서비스 제공 외 목적으로 사용하거나 제3자에게 판매하지 않습니다.\n\n전체 처리방침은 https://vibepick.github.io/privacy.html 에서 확인할 수 있습니다."
                ),
                InfoSection(
                    title: "데이터 출처",
                    body: "시세·뉴스·종목 데이터는 외부 데이터 제공사로부터 받아 가공되며, 실시간성·정확성은 제공사 정책에 따릅니다. 자세한 출처는 각 토픽 하단에서 확인할 수 있습니다."
                )
            ]
        }
    }
}

struct InfoSection: Identifiable {
    let id = UUID()
    let title: String
    let body: String
}

// MARK: - Info Detail View
struct InfoDetailView: View {
    let page: InfoPage

    var body: some View {
        ZStack {
            VPTheme.background.ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    Text(page.title)
                        .font(.system(size: 22, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.top, 6)

                    ForEach(page.sections) { section in
                        InfoSectionCard(section: section)
                    }
                }
                .padding(.horizontal, 18)
                .padding(.bottom, 32)
            }
        }
        .navigationTitle("")
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(VPTheme.background, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .toolbarColorScheme(.dark, for: .navigationBar)
    }
}

struct InfoSectionCard: View {
    let section: InfoSection

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(section.title)
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.white)

            Text(section.body)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(VPTheme.textSecondary)
                .lineSpacing(5)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(VPTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.white.opacity(0.05), lineWidth: 1))
    }
}

#Preview {
    NavigationStack {
        InfoDetailView(page: .appInfo)
    }
}
