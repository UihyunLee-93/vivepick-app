import Foundation

enum NetworkError: Error {
    case invalidResponse
    case serverError(Int)
    case decodingError(Error)
}

final class NetworkManager {
    static let shared = NetworkManager()

    private let baseURL = "https://vivepick-app-production.up.railway.app"

    private init() {}

    func fetchBriefings() async throws -> [Brief] {
        guard let url = URL(string: "\(baseURL)/briefings?limit=20") else {
            throw URLError(.badURL)
        }

        return try await fetchData(from: url)
    }

    private func fetchData<T: Decodable>(from url: URL) async throws -> T {
        print("🌐 API 요청: \(url.absoluteString)")

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ 응답 오류: invalidResponse")
            throw NetworkError.invalidResponse
        }

        print("✅ HTTP 상태: \(httpResponse.statusCode)")

        guard (200...299).contains(httpResponse.statusCode) else {
            print("❌ 서버 오류: \(httpResponse.statusCode)")
            throw NetworkError.serverError(httpResponse.statusCode)
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            print("❌ JSON 디코딩 오류: \(error)")
            print("📦 받은 데이터: \(String(data: data, encoding: .utf8) ?? "nil")")
            throw NetworkError.decodingError(error)
        }
    }
}
