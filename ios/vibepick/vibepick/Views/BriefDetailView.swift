import SwiftUI

// MARK: - 03. Brief Detail (Unlocked)
struct BriefDetailView: View {
    let group: BriefSlotGroup
    @AppStorage(AppMode.isProModeStorageKey) private var isProMode = false
    @AppStorage(BriefCategory.selectedCategoriesStorageKey) private var selectedCategoryIDs = BriefCategory.defaultSelectedCategoryIDs
    @Environment(\.dismiss) private var dismiss

    private var slot: BriefSlot { group.slot }

    private var enabledCategories: Set<BriefCategory> {
        BriefCategory.categories(from: selectedCategoryIDs, limit: categoryLimit)
    }

    private var categoryLimit: Int? {
        isProMode ? nil : AppMode.regularCategoryLimit
    }

    private var filteredBriefs: [Brief] {
        group.briefs.filter { brief in
            brief.categories.isEmpty
                || brief.categories.contains(where: { enabledCategories.contains($0) })
        }
    }

    var body: some View {
        ZStack {
            VPTheme.background.ignoresSafeArea()
            slotBackdrop
                .ignoresSafeArea()

            VStack(spacing: 0) {
                topBar
                    .padding(.horizontal, 16)
                    .padding(.top, 6)
                    .padding(.bottom, 10)

                ScrollView {
                    VStack(spacing: 12) {
                        if filteredBriefs.isEmpty {
                            emptyState
                        } else {
                            ForEach(filteredBriefs) { brief in
                                NavigationLink {
                                    CardDetailView(brief: brief)
                                } label: {
                                    BriefRow(brief: brief)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 12)
                    .padding(.bottom, 24)
                }
            }
        }
        .navigationBarHidden(true)
    }

    private var slotBackdrop: some View {
        ZStack(alignment: .topTrailing) {
            LinearGradient(
                colors: slot.fullBackdropColors,
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            LinearGradient(
                colors: slot.backdropColors,
                startPoint: .top,
                endPoint: .bottom
            )
            .frame(height: 280)
            .frame(maxHeight: .infinity, alignment: .top)

            Image(systemName: slot.backdropSymbol)
                .font(.system(size: 150, weight: .bold))
                .foregroundColor(.white.opacity(0.075))
                .offset(x: 30, y: 84)

            Image(systemName: slot.backdropSymbol)
                .font(.system(size: 220, weight: .bold))
                .foregroundColor(.white.opacity(0.025))
                .offset(x: 72, y: 410)

            VStack(spacing: 20) {
                ForEach(0..<7, id: \.self) { index in
                    Capsule()
                        .fill(Color.white.opacity(0.055))
                        .frame(width: CGFloat(190 - index * 18), height: 2)
                }
            }
            .rotationEffect(.degrees(-18))
            .offset(x: -22, y: 144)
        }
    }

    private var emptyState: some View {
        VStack(spacing: 10) {
            Image(systemName: "line.3.horizontal.decrease.circle")
                .font(.system(size: 28, weight: .semibold))
                .foregroundColor(VPTheme.textTertiary)

            Text("선택한 카테고리에 해당하는 토픽이 없습니다")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.white.opacity(0.86))
                .multilineTextAlignment(.center)

            Text("설정에서 관심 카테고리를 변경하면 카드 목록에 바로 반영됩니다.")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(VPTheme.textTertiary)
                .multilineTextAlignment(.center)
                .lineSpacing(3)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 48)
        .padding(.horizontal, 20)
        .background(VPTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.white.opacity(0.06), lineWidth: 1))
    }

    private var topBar: some View {
        HStack(spacing: 10) {
            Button {
                dismiss()
            } label: {
                Image(systemName: "chevron.left")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white.opacity(0.86))
                    .frame(width: 34, height: 34)
                    .background(.ultraThinMaterial)
                    .background(Color.white.opacity(0.05))
                    .clipShape(Circle())
                    .overlay(Circle().stroke(Color.white.opacity(0.08), lineWidth: 1))
            }

            Spacer()

            HStack(spacing: 6) {
                Text(slot.emoji)
                    .font(.system(size: 13))
                Text("\(slot.time) \(slot.title)")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.white)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 7)
            .background(.ultraThinMaterial)
            .background(Color.white.opacity(0.04))
            .clipShape(Capsule())
            .overlay(Capsule().stroke(Color.white.opacity(0.08), lineWidth: 1))

            Spacer()

            Color.clear.frame(width: 34, height: 34)
        }
    }

}

// MARK: - Brief Row
struct BriefRow: View {
    let brief: Brief

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                HStack(spacing: 6) {
                    Image(systemName: brief.primaryCategory.iconName)
                        .font(.system(size: 10.5, weight: .bold))
                        .foregroundColor(brief.primaryCategory.color)
                        .frame(width: 13)

                    Text(brief.categoryLabel)
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(brief.primaryCategory.color)
                }
                .padding(.horizontal, 9)
                .padding(.vertical, 5)
                .background(brief.primaryCategory.color.opacity(0.15))
                .clipShape(Capsule())

                Spacer()

                Text("\(brief.mood.rawValue) \(brief.mood.arrow)")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(brief.mood.color)
                    .padding(.horizontal, 7)
                    .padding(.vertical, 3)
                    .background(brief.mood.color.opacity(0.14))
                    .clipShape(Capsule())
            }

            Text(brief.title)
                .font(.system(size: 15, weight: .bold))
                .foregroundColor(.white)
                .multilineTextAlignment(.leading)
                .lineLimit(2)
                .fixedSize(horizontal: false, vertical: true)

        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(VPTheme.surface)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color.white.opacity(0.06), lineWidth: 1)
        )
    }
}

// MARK: - 05/06. Locked Brief
struct LockedBriefView: View {
    let slot: BriefSlot
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            VPTheme.background.ignoresSafeArea()

            // Soft slot-tinted glow
            RadialGradient(
                colors: [VPTheme.purple.opacity(0.22), .clear],
                center: .center, startRadius: 30, endRadius: 320
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                lockedTopBar
                    .padding(.horizontal, 16)
                    .padding(.top, 6)

                Spacer()

                VStack(spacing: 18) {
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [VPTheme.purple.opacity(0.3), VPTheme.pink.opacity(0.18)],
                                    startPoint: .topLeading, endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 96, height: 96)
                            .shadow(color: VPTheme.purple.opacity(0.4), radius: 28)

                        Image(systemName: "lock.fill")
                            .font(.system(size: 34, weight: .semibold))
                            .foregroundColor(.white)
                    }

                    VStack(spacing: 8) {
                        Text("준비 중인 브리핑입니다")
                            .font(.system(size: 18, weight: .bold))
                            .foregroundColor(.white)

                        Text("\(slot.title)는 곧 확인할 수 있도록 준비하고 있습니다.")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(VPTheme.textSecondary)
                            .multilineTextAlignment(.center)
                            .lineSpacing(3)
                    }
                }

                Spacer()
            }
        }
        .navigationBarHidden(true)
    }

    private var lockedTopBar: some View {
        HStack {
            Button { dismiss() } label: {
                Image(systemName: "chevron.left")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white.opacity(0.86))
                    .frame(width: 34, height: 34)
                    .background(.ultraThinMaterial)
                    .background(Color.white.opacity(0.05))
                    .clipShape(Circle())
                    .overlay(Circle().stroke(Color.white.opacity(0.08), lineWidth: 1))
            }

            Spacer()

            HStack(spacing: 6) {
                Text(slot.emoji)
                    .font(.system(size: 13))
                Text("\(slot.time) \(slot.title)")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.white)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 7)
            .background(.ultraThinMaterial)
            .background(Color.white.opacity(0.04))
            .clipShape(Capsule())
            .overlay(Capsule().stroke(Color.white.opacity(0.08), lineWidth: 1))

            Spacer()

            Color.clear.frame(width: 34, height: 34)
        }
    }
}

#Preview("Detail") {
    NavigationStack {
        BriefDetailView(group: DummyData.slotGroups(isProMode: true)[0])
    }
}

#Preview("Locked") {
    NavigationStack {
        LockedBriefView(slot: .noon)
    }
}
