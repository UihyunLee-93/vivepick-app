import SwiftUI

// MARK: - 02. Settings
struct SettingsView: View {
    @AppStorage(NotificationPreferenceKey.morning) private var morningOn = true
    @AppStorage(NotificationPreferenceKey.noon) private var noonOn = false
    @AppStorage(NotificationPreferenceKey.night) private var nightOn = false
    @AppStorage(AppMode.isProModeStorageKey) private var isProMode = false
    private let showsProControls = false
    @AppStorage(BriefCategory.selectedCategoriesStorageKey) private var selectedCategoryIDs = BriefCategory.defaultSelectedCategoryIDs

    var body: some View {
        NavigationStack {
            ZStack {
                VPTheme.background.ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: 18) {
                        header
#if DEBUG
                        if showsProControls {
                            proCard
                            devModeSection
                        }
#endif
                        notificationSection
                        categorySection
#if DEBUG
                        if showsProControls {
                            subscriptionSection
                        }
#endif
                        infoSection
                        footer
                    }
                    .padding(.horizontal, 18)
                    .padding(.top, 14)
                    .padding(.bottom, 30)
                }
            }
            .toolbarBackground(VPTheme.background, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbarColorScheme(.dark, for: .navigationBar)
        }
        .tint(VPTheme.purple)
        .onChange(of: morningOn) { _, isEnabled in
            updateNotification(for: .morning, isEnabled: isEnabled)
        }
        .onChange(of: noonOn) { _, isEnabled in
            updateNotification(for: .noon, isEnabled: isEnabled && (isProMode || !showsProControls))
        }
        .onChange(of: nightOn) { _, isEnabled in
            updateNotification(for: .night, isEnabled: isEnabled && (isProMode || !showsProControls))
        }
    }

    private var header: some View {
        HStack {
            Text("설정")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.white)

            Spacer()

            Text("v1.0.0")
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(VPTheme.textMuted)
        }
    }

#if DEBUG
    // MARK: Pro upgrade card
    private var proCard: some View {
        HStack(spacing: 14) {
            ZStack {
                RoundedRectangle(cornerRadius: 14)
                    .fill(
                        LinearGradient(
                            colors: [VPTheme.purple, VPTheme.pink],
                            startPoint: .topLeading, endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 48, height: 48)
                Image(systemName: "crown.fill")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(.white)
            }

            VStack(alignment: .leading, spacing: 5) {
                Text("VibePick 프로")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)

                Text(isProMode ? "모든 브리핑 · 카테고리 전체 선택 가능" : "아침 브리핑만 열람 · 카테고리 3개")
                    .font(.system(size: 11.5, weight: .medium))
                    .foregroundColor(VPTheme.textTertiary)
                    .lineLimit(1)
            }

            Spacer()

            Button {
                isProMode = true
            } label: {
                Text(isProMode ? "프로 사용중" : "업그레이드")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 9)
                    .background(
                        LinearGradient(
                            colors: [VPTheme.purple, VPTheme.pink],
                            startPoint: .leading, endPoint: .trailing
                        )
                    )
                    .clipShape(Capsule())
                    .shadow(color: VPTheme.purple.opacity(0.5), radius: 10, y: 4)
            }
        }
        .padding(14)
        .background(
            LinearGradient(
                colors: [VPTheme.purple.opacity(0.22), VPTheme.pink.opacity(0.10), VPTheme.surface],
                startPoint: .leading, endPoint: .trailing
            )
        )
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .overlay(
            RoundedRectangle(cornerRadius: 20).stroke(VPTheme.purple.opacity(0.25), lineWidth: 1)
        )
    }

    // MARK: Dev mode section
    private var devModeSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionLabel("임시 구독 모드")

            HStack(spacing: 12) {
                Image(systemName: isProMode ? "crown.fill" : "person.fill")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(isProMode ? VPTheme.proGold : VPTheme.textSecondary)
                    .frame(width: 28, height: 28)
                    .background(Color.white.opacity(0.05))
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                VStack(alignment: .leading, spacing: 3) {
                    Text(isProMode ? "프로 모드" : "일반 모드")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.white)

                    Text(isProMode ? "아침·점심·저녁 브리핑과 모든 카테고리 선택 가능" : "아침 브리핑만 열람 가능, 카테고리 최대 3개")
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(VPTheme.textTertiary)
                        .lineLimit(2)
                }

                Spacer()

                Toggle("", isOn: $isProMode)
                    .labelsHidden()
                    .tint(VPTheme.purple)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(VPTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.white.opacity(0.05), lineWidth: 1))
        }
        .onChange(of: isProMode) { _, _ in
            enforceCategoryLimitIfNeeded()
            updateLockedNotificationPreferencesIfNeeded()
        }
        .onAppear {
            enforceCategoryLimitIfNeeded()
        }
    }

#endif

    // MARK: Notification section
    private var notificationSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionLabel("알림")

            VStack(spacing: 0) {
                BriefToggleRow(slot: .morning, isOn: $morningOn, isLocked: false)
                divider
                BriefToggleRow(slot: .noon, isOn: $noonOn, isLocked: showsProControls && !isProMode)
                divider
                BriefToggleRow(slot: .night, isOn: $nightOn, isLocked: showsProControls && !isProMode)
            }
            .padding(.horizontal, 14)
            .background(VPTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.white.opacity(0.05), lineWidth: 1))
        }
    }

    // MARK: Category section
    private var categorySection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                sectionLabel("카테고리")
                Spacer()
                Text(categoryCountText)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(VPTheme.textTertiary)
            }

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 132), spacing: 8)], alignment: .leading, spacing: 8) {
                ForEach(BriefCategory.selectableCategories) { category in
                    let isSelected = selectedCategories.contains(category)
                    CategoryFilterButton(
                        category: category,
                        isSelected: isSelected,
                        isDisabled: !isSelected && !canSelectMoreCategories
                    ) {
                        toggleCategory(category)
                    }
                }
            }
            .padding(14)
            .background(VPTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.white.opacity(0.05), lineWidth: 1))
        }
    }

    private var selectedCategories: Set<BriefCategory> {
        BriefCategory.categories(from: selectedCategoryIDs, limit: categoryLimit)
    }

    private var categoryLimit: Int? {
        if !showsProControls { return nil }
        return isProMode ? nil : AppMode.regularCategoryLimit
    }

    private var categoryCountText: String {
        if !showsProControls || isProMode {
            return "\(selectedCategories.count)/\(BriefCategory.selectableCategories.count) 선택"
        }

        return "\(selectedCategories.count)/\(AppMode.regularCategoryLimit) 선택"
    }

    private var canSelectMoreCategories: Bool {
        !showsProControls || isProMode || selectedCategories.count < AppMode.regularCategoryLimit
    }

    private func toggleCategory(_ category: BriefCategory) {
        var categories = selectedCategories

        if categories.contains(category) {
            guard categories.count > 1 else { return }
            categories.remove(category)
        } else {
            guard canSelectMoreCategories else { return }
            categories.insert(category)
        }

        selectedCategoryIDs = BriefCategory.storageValue(for: categories, limit: categoryLimit)
    }

    private func enforceCategoryLimitIfNeeded() {
        selectedCategoryIDs = BriefCategory.storageValue(for: selectedCategories, limit: categoryLimit)
    }

    private func updateNotification(for slot: BriefSlot, isEnabled: Bool) {
        Task {
            await NotificationService.shared.updateDailyNotification(for: slot, isEnabled: isEnabled)
        }
    }

    private func scheduleCurrentNotifications() {
        updateNotification(for: .morning, isEnabled: morningOn)
        updateNotification(for: .noon, isEnabled: noonOn && (isProMode || !showsProControls))
        updateNotification(for: .night, isEnabled: nightOn && (isProMode || !showsProControls))
    }

    private func updateLockedNotificationPreferencesIfNeeded() {
        if showsProControls && !isProMode {
            noonOn = false
            nightOn = false
        }

        scheduleCurrentNotifications()
    }

#if DEBUG
    // MARK: Subscription section
    private var subscriptionSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionLabel("구독")

            VStack(spacing: 0) {
                SettingsRow(icon: "creditcard", title: "구독 관리", trailing: isProMode ? "프로 플랜" : "무료 플랜")
                divider
                SettingsRow(icon: "arrow.clockwise", title: "구매 복원")
            }
            .padding(.horizontal, 14)
            .background(VPTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.white.opacity(0.05), lineWidth: 1))
        }
    }

#endif

    // MARK: Info section
    private var infoSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionLabel("정보")

            VStack(spacing: 0) {
                NavigationLink {
                    InfoDetailView(page: .appInfo)
                } label: {
                    SettingsRow(icon: "info.circle", title: "앱 정보 · 투자 유의사항")
                }
                .buttonStyle(.plain)

                divider

                NavigationLink {
                    InfoDetailView(page: .help)
                } label: {
                    SettingsRow(icon: "questionmark.circle", title: "도움말")
                }
                .buttonStyle(.plain)

                divider

                NavigationLink {
                    InfoDetailView(page: .terms)
                } label: {
                    SettingsRow(icon: "doc.text", title: "이용약관 · 개인정보")
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 14)
            .background(VPTheme.surface)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.white.opacity(0.05), lineWidth: 1))
        }
    }

    private var footer: some View {
        Text("VibePick · 하루 3번 시장 브리핑")
            .font(.system(size: 10, weight: .semibold))
            .tracking(0.4)
            .foregroundColor(VPTheme.textMuted)
            .frame(maxWidth: .infinity)
            .padding(.top, 6)
    }

    private func sectionLabel(_ text: String) -> some View {
        Text(text)
            .font(.system(size: 12, weight: .bold))
            .tracking(0.5)
            .foregroundColor(VPTheme.textTertiary)
            .padding(.leading, 4)
    }

    private var divider: some View {
        Rectangle()
            .fill(Color.white.opacity(0.05))
            .frame(height: 1)
    }
}

// MARK: - Category Filter Button
struct CategoryFilterButton: View {
    let category: BriefCategory
    let isSelected: Bool
    let isDisabled: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: category.iconName)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(isSelected ? category.color : (isDisabled ? VPTheme.textMuted : VPTheme.textTertiary))
                    .frame(width: 16)

                Text(category.rawValue)
                    .font(.system(size: 12.5, weight: .semibold))
                    .foregroundColor(isSelected ? .white : (isDisabled ? VPTheme.textMuted : VPTheme.textTertiary))
                    .lineLimit(1)
                    .minimumScaleFactor(0.85)

                Spacer(minLength: 0)

                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(isSelected ? category.color : VPTheme.textMuted)
            }
            .frame(height: 38)
            .padding(.horizontal, 11)
            .background(isSelected ? category.color.opacity(0.16) : Color.white.opacity(isDisabled ? 0.02 : 0.04))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? category.color.opacity(0.42) : Color.white.opacity(0.06), lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(.plain)
        .disabled(isDisabled)
        .opacity(isDisabled ? 0.55 : 1)
    }
}

// MARK: - Brief Toggle Row
struct BriefToggleRow: View {
    let slot: BriefSlot
    @Binding var isOn: Bool
    let isLocked: Bool

    var body: some View {
        HStack(spacing: 12) {
            Text(slot.emoji)
                .font(.system(size: 16))
                .frame(width: 28, height: 28)
                .background(Color.white.opacity(0.05))
                .clipShape(RoundedRectangle(cornerRadius: 8))

            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 6) {
                    Text(slot.title)
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.white)

                    if isLocked {
                        Image(systemName: "lock.fill")
                            .font(.system(size: 8, weight: .bold))
                            .foregroundColor(VPTheme.textTertiary)
                    }
                }

                Text("매일 \(slot.time)")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(VPTheme.textTertiary)
            }

            Spacer()

            if isLocked {
                Text("프로")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(
                        LinearGradient(
                            colors: [VPTheme.purple, VPTheme.pink],
                            startPoint: .leading, endPoint: .trailing
                        )
                    )
                    .clipShape(Capsule())
            } else {
                Toggle("", isOn: $isOn)
                    .labelsHidden()
                    .tint(VPTheme.purple)
            }
        }
        .padding(.vertical, 12)
    }
}

// MARK: - Settings Row
struct SettingsRow: View {
    let icon: String
    let title: String
    var trailing: String? = nil

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(VPTheme.textSecondary)
                .frame(width: 28, height: 28)
                .background(Color.white.opacity(0.05))
                .clipShape(RoundedRectangle(cornerRadius: 8))

            Text(title)
                .font(.system(size: 13.5, weight: .semibold))
                .foregroundColor(.white.opacity(0.86))

            Spacer()

            if let trailing {
                Text(trailing)
                    .font(.system(size: 11.5, weight: .semibold))
                    .foregroundColor(VPTheme.textTertiary)
            }

            Image(systemName: "chevron.right")
                .font(.system(size: 10, weight: .bold))
                .foregroundColor(VPTheme.textMuted)
        }
        .padding(.vertical, 12)
    }
}

#Preview {
    SettingsView()
}
