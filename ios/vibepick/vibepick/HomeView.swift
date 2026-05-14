import SwiftUI

// MARK: - 02. Home View
struct HomeView: View {
    @State private var selectedVibe: Vibe?
    @State private var searchText = ""
    
    var filteredVibes: [Vibe] {
        if searchText.isEmpty {
            return DummyData.vibes
        }
        return DummyData.vibes.filter { 
            $0.tag.lowercased().contains(searchText.lowercased()) ||
            $0.title.lowercased().contains(searchText.lowercased())
        }
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                // 배경
                Color(red: 0.1, green: 0.08, blue: 0.15)
                    .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // 헤더
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("오늘의 시장 분위기")
                                    .font(.system(size: 16, weight: .semibold))
                                    .foregroundColor(.white)
                                
                                Text("업데이트 06:20")
                                    .font(.system(size: 12, weight: .regular))
                                    .foregroundColor(.white.opacity(0.5))
                            }
                            
                            Spacer()
                            
                            Button(action: {}) {
                                Image(systemName: "bell.fill")
                                    .font(.system(size: 18))
                                    .foregroundColor(.white)
                            }
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.vertical, 16)
                    
                    // 검색바
                    SearchBar(text: $searchText)
                        .padding(.horizontal, 20)
                        .padding(.bottom, 20)
                    
                    // 관심 태그 섹션
                    VStack(alignment: .leading, spacing: 12) {
                        Text("관심 태그")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.white)
                            .padding(.horizontal, 20)
                        
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 10) {
                                ForEach(filteredVibes.prefix(5)) { vibe in
                                    NavigationLink(destination: TagDetailView(vibe: vibe)) {
                                        VibeCardSmall(vibe: vibe)
                                    }
                                }
                            }
                            .padding(.horizontal, 20)
                        
                        }
                    }
                    .padding(.bottom, 20)
                    
                    // 모든 바이브
                    VStack(alignment: .leading, spacing: 12) {
                        Text("모든 바이브")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.white)
                            .padding(.horizontal, 20)
                        
                        ScrollView {
                            VStack(spacing: 12) {
                                ForEach(filteredVibes, id: \.id) { vibe in
                                    NavigationLink(destination: TagDetailView(vibe: vibe)) {
                                        VibeRowItem(vibe: vibe)
                                    }
                                }
                            }
                            .padding(.horizontal, 20)
                            .padding(.vertical, 12)
                        }
                    }
                }
            }
            .navigationBarHidden(true)
        }
    }
}

// MARK: - Vibe Card (Small)
struct VibeCardSmall: View {
    let vibe: Vibe
    
    var body: some View {
        HStack(spacing: 10) {
            
            Image(systemName: vibe.state.icon)
                .font(.system(size: 18, weight: .medium))
                .foregroundColor(vibe.state.color)
            
            VStack(alignment: .leading, spacing: 2) {
                
                Text(vibe.tag)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.white)
                
                Text(vibe.state.rawValue)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(vibe.state.color.opacity(0.9))
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(vibe.state.color.opacity(0.12))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(vibe.state.color.opacity(0.25), lineWidth: 1)
        )
    }
}

// MARK: - Vibe Row Item
struct VibeRowItem: View {
    let vibe: Vibe
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: vibe.state.icon)
                .font(.system(size: 32))
                .foregroundColor(vibe.state.color)
            
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 8) {
                    Text(vibe.title)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(.white)
                    
                    Text(vibe.state.rawValue)
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundColor(vibe.state.color)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(vibe.state.color.opacity(0.2))
                        .cornerRadius(4)
                }
                
                Text(vibe.summary)
                    .font(.system(size: 12, weight: .regular))
                    .foregroundColor(.white.opacity(0.6))
                    .lineLimit(1)
            }
            
            Spacer()
            
            // 미니 차트
            VStack(spacing: 2) {
                ForEach(0..<3, id: \.self) { index in
                    RoundedRectangle(cornerRadius: 1.5)
                        .fill(vibe.state.color.opacity(0.4 + Double(index) * 0.3))
                        .frame(height: 6)
                }
            }
            .frame(width: 18)
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.white.opacity(0.04))
        )
    }
}

// MARK: - Search Bar
struct SearchBar: View {
    @Binding var text: String
    
    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.white.opacity(0.5))
            
            TextField("비브 검색", text: $text)
                .foregroundColor(.white)
                .font(.system(size: 14))
            
            if !text.isEmpty {
                Button(action: { text = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 14))
                        .foregroundColor(.white.opacity(0.5))
                }
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(Color.white.opacity(0.06))
        )
    }
}

#Preview {
    HomeView()
}
