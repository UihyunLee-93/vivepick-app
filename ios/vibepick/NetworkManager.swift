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

    // ✅ FINAL 버전: BriefingResponse → Brief 변환 포함
    func fetchBriefings(timeSlot: BriefSlot? = nil) async throws -> [Brief] {
        var components = URLComponents(string: "\(baseURL)/briefings")
        var queryItems = [URLQueryItem(name: "limit", value: "20")]

        if let timeSlot {
            queryItems.append(URLQueryItem(name: "time_slot", value: timeSlot.rawValue))
        }

        components?.queryItems = queryItems

        guard let url = components?.url else {
            throw URLError(.badURL)
        }

        let responses: [BriefingResponse] = try await fetchData(from: url)
        return responses.enumerated().map { index, response in
            response.toBrief(topicNumber: index + 1)
        }
    }

    // ✅ 추가: 크롤링 트리거 (당신 코드)
    func triggerCrawl() async throws -> [String: Any] {
        guard let url = URL(string: "\(baseURL)/trigger-crawl") else {
            throw URLError(.badURL)
        }

        return try await fetchJSONDictionary(from: url)
    }

    // ✅ 당신의 코드: 강화된 날짜 파싱
    private func fetchData<T: Decodable>(from url: URL) async throws -> T {
        let data = try await requestData(from: url)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let raw = try container.decode(String.self)

            let formatter = DateFormatter()
            formatter.locale = Locale(identifier: "en_US_POSIX")
            formatter.timeZone = TimeZone(identifier: "UTC")

            formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
            if let date = formatter.date(from: raw) { return date }

            formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
            if let date = formatter.date(from: raw) { return date }

            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "지원하지 않는 날짜 형식: \(raw)"
            )
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            print("❌ JSON 디코딩 오류: \(error)")
            print("📦 받은 데이터: \(String(data: data, encoding: .utf8) ?? "nil")")
            throw NetworkError.decodingError(error)
        }
    }

    // ✅ 당신의 코드: Dictionary 파싱 (triggerCrawl용)
    private func fetchJSONDictionary(from url: URL) async throws -> [String: Any] {
        let data = try await requestData(from: url)

        do {
            let object = try JSONSerialization.jsonObject(with: data)
            guard let dictionary = object as? [String: Any] else {
                print("❌ JSON 형식 오류: dictionary가 아닙니다")
                throw NetworkError.invalidResponse
            }

            print("📦 받은 데이터: \(dictionary)")
            return dictionary
        } catch let error as NetworkError {
            throw error
        } catch {
            print("❌ JSON 파싱 오류: \(error)")
            print("📦 받은 데이터: \(String(data: data, encoding: .utf8) ?? "nil")")
            throw NetworkError.decodingError(error)
        }
    }

    // ✅ 당신의 코드: HTTP 요청 처리
    private func requestData(from url: URL) async throws -> Data {
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

        return data
    }
}
