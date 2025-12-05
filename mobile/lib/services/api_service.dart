import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/models.dart';

class ClientApiService {
  ClientApiService({
    http.Client? client,
    String? baseUrl,
  })  : client = client ?? http.Client(),
        baseUrl = baseUrl ??
            const String.fromEnvironment(
              'SMARTGATE_API_BASE',
              defaultValue: 'http://localhost:60000/api',
            );

  final http.Client client;
  final String baseUrl;
  String? _token;

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  void setToken(String? token) {
    _token = token;
  }

  Map<String, String> _headers({bool json = false}) {
    final headers = <String, String>{};
    if (_token != null && _token!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $_token';
    }
    if (json) {
      headers['Content-Type'] = 'application/json';
    }
    return headers;
  }

  Future<AuthResponse> signupPortal(PortalSignupPayload payload) async {
    final response = await client.post(
      _uri('/auth/signup'),
      headers: _headers(json: true),
      body: jsonEncode(payload.toJson()),
    );
    _throwIfNeeded(response);
    return AuthResponse.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<AuthResponse> loginPortal({required String identifier, required String password}) async {
    final response = await client.post(
      _uri('/auth/login'),
      headers: _headers(json: true),
      body: jsonEncode({'identifier': identifier, 'password': password}),
    );
    _throwIfNeeded(response);
    return AuthResponse.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<ClientRegistrationResponse> register(ClientRegistrationPayload payload) async {
    final response = await client.post(
      _uri('/client/register'),
      headers: _headers(json: true),
      body: jsonEncode(payload.toJson()),
    );
    _throwIfNeeded(response);
    return ClientRegistrationResponse.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<ClientSummary> fetchSummary(String userId) async {
    final response = await client.get(_uri('/client/summary/$userId'), headers: _headers());
    _throwIfNeeded(response);
    return ClientSummary.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<WalletActivity> fetchWallet(String userId) async {
    final response = await client.get(_uri('/client/wallet/$userId'), headers: _headers());
    _throwIfNeeded(response);
    return WalletActivity.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<WalletActivity> topUpWallet(String userId, double amount) async {
    final response = await client.post(
      _uri('/client/wallet/$userId/top-up'),
      headers: _headers(json: true),
      body: jsonEncode({'amount': amount, 'source': 'card'}),
    );
    _throwIfNeeded(response);
    return WalletActivity.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<RoleUpgradeRequest> submitRoleUpgrade(String userId, String targetRole, String reason) async {
    final response = await client.post(
      _uri('/client/role-upgrade/$userId'),
      headers: _headers(json: true),
      body: jsonEncode({'target_role': targetRole, 'reason': reason, 'attachments': <String>[]}),
    );
    _throwIfNeeded(response);
    return RoleUpgradeRequest.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<GuestLookupResponse> lookupGuestSession({String? sessionId, String? plateText}) async {
    final uri = _uri('/client/guest/lookup').replace(queryParameters: {
      if (sessionId != null && sessionId.isNotEmpty) 'session_id': sessionId,
      if (plateText != null && plateText.isNotEmpty) 'plate_text': plateText,
    });
    final response = await client.get(uri, headers: _headers());
    _throwIfNeeded(response);
    return GuestLookupResponse.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<Payment> payGuestSession({
    required String sessionId,
    double? amount,
    required String paymentSource,
    String? userId,
  }) async {
    final response = await client.post(
      _uri('/client/guest/pay'),
      headers: _headers(json: true),
      body: jsonEncode({
        'session_id': sessionId,
        if (amount != null) 'amount': amount,
        'payment_source': paymentSource,
        if (userId != null) 'user_id': userId,
      }),
    );
    _throwIfNeeded(response);
    return Payment.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<ParkingOverview> fetchParkingOverview() async {
    final response = await client.get(_uri('/client/parking'), headers: _headers());
    _throwIfNeeded(response);
    return ParkingOverview.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<ParkingPass> payPassInvoice(String passId, String userId) async {
    final uri = _uri('/client/pass/$passId/pay').replace(queryParameters: {'user_id': userId});
    final response = await client.post(uri, headers: _headers());
    _throwIfNeeded(response);
    return ParkingPass.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<List<ParkingVenue>> fetchParkingVenues() async {
    final response = await client.get(_uri('/parking/venues'), headers: _headers());
    _throwIfNeeded(response);
    final data = jsonDecode(response.body) as List<dynamic>;
    return data.map((e) => ParkingVenue.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ParkingVenue> sendParkingEvent(String venueId, String direction) async {
    final response = await client.post(
      _uri('/parking/event'),
      headers: _headers(json: true),
      body: jsonEncode({'venue_id': venueId, 'direction': direction}),
    );
    _throwIfNeeded(response);
    return ParkingVenue.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<List<AppNotification>> fetchNotifications(String userId) async {
    final response = await client.get(_uri('/client/notifications/$userId'), headers: _headers());
    _throwIfNeeded(response);
    final data = jsonDecode(response.body) as List<dynamic>;
    return data.map((e) => AppNotification.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<AppNotification> acknowledgeNotification(String userId, String notificationId) async {
    final response = await client.post(
      _uri('/client/notifications/$userId/ack'),
      headers: _headers(json: true),
      body: jsonEncode({'notification_id': notificationId}),
    );
    _throwIfNeeded(response);
    return AppNotification.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  void _throwIfNeeded(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    final body = response.body;
    final detail = body.isNotEmpty ? body : response.reasonPhrase;
    throw Exception('Request failed: ${response.statusCode} $detail');
  }

  void dispose() {
    client.close();
  }
}
