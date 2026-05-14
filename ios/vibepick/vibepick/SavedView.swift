import SwiftUI

struct SavedView: View {
    @State private var selectedFilter = "전체"
    private let filters = ["전체", "태그", "브리핑"]
    private let savedVibes = DummyData.userProfile.savedVibes

    var body: some View {
        ZStack {
            VPTheme.background.ignoresSafeArea()

            VStack(spacing: 0) {
                header
                filterBar

                ScrollView {
                    VStack(spacing: 12) {
                        ForEach(savedVibes) { saved in
                            SavedVibeCard(savedVibe: saved)
                        }
                    }
                    .padding(.horizontal, 18)
                    .padding(.top, 16)
                    .padding(.bottom, 28)
                }
            }
        }
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 3) {
                Text("MOOD LIBRARY")
                    .font(.system(size: 10, weight: .bold))
                    .tracking(1.3)
                    .foregroundColor(.white.opacity(0.34))

                Text("저장한 흐름")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(.white)
            }

            Spacer()

            Button("편집") {}
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(.white.opacity(0.58))
        }
        .padding(.horizontal, 18)
        .padding(.top, 16)
        .padding(.bottom, 12)
    }

    private var filterBar: some View {
        HStack(spacing: 6) {
            ForEach(filters, id: \.self) { filter in
                Button {
                    selectedFilter = filter
                } label: {
                    Text(filter)
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(selectedFilter == filter ? .white : .white.opacity(0.42))
                        .frame(maxWidth: .infinity)
                        .frame(height: 34)
                        .background(selectedFilter == filter ? VPTheme.cardSoft : Color.clear)
                        .clipShape(RoundedRectangle(cornerRadius: 9))
                }
            }
        }
        .padding(4)
        .background(VPTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .padding(.horizontal, 18)
    }
}

struct SavedVibeCard: View {
    let savedVibe: SavedVibe

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: savedVibe.vibe.state.icon)
                .font(.system(size: 15, weight: .bold))
                .foregroundColor(savedVibe.vibe.state.color)
                .frame(width: 34, height: 34)
                .background(savedVibe.vibe.state.color.opacity(0.12))
                .clipShape(RoundedRectangle(cornerRadius: 10))

            VStack(alignment: .leading, spacing: 5) {
                HStack(spacing: 6) {
                    Text(savedVibe.vibe.tag)
                        .font(.system(size: 13, weight: .bold))
                        .foregroundColor(.white)

                    Text(savedVibe.vibe.state.rawValue)
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(savedVibe.vibe.state.color)
                }

                Text(savedVibe.memo.isEmpty ? savedVibe.vibe.summary : savedVibe.memo)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.white.opacity(0.58))
            }

            Spacer()

            Text(relativeDate(savedVibe.savedDate))
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(.white.opacity(0.34))

            Image(systemName: "chevron.right")
                .font(.system(size: 11, weight: .bold))
                .foregroundColor(.white.opacity(0.28))
        }
        .padding(14)
        .background(VPTheme.card)
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }

    private func relativeDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "M월 d일"
        return formatter.string(from: date)
    }
}

#Preview {
    SavedView()
}
