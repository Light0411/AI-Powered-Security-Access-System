import 'package:intl/intl.dart';

DateTime? parseDate(String? value) {
  if (value == null || value.isEmpty) return null;
  try {
    return DateTime.parse(value).toLocal();
  } catch (_) {
    return null;
  }
}

String formatDisplayDate(DateTime? date) {
  if (date == null) return 'n/a';
  return DateFormat('dd MMM yyyy').format(date);
}

class ClientRegistrationPayload {
  ClientRegistrationPayload({
    required this.name,
    required this.email,
    required this.phone,
    required this.programme,
    required this.role,
    required this.planType,
    required this.vehicles,
  });

  final String name;
  final String email;
  final String phone;
  final String programme;
  final String role;
  final String planType;
  final List<String> vehicles;

  Map<String, dynamic> toJson() => {
        'name': name,
        'email': email,
        'phone': phone,
        'programme': programme,
        'role': role,
        'plan_type': planType,
        'vehicles': vehicles,
      };
}

class ClientRegistrationResponse {
  ClientRegistrationResponse({
    required this.registrationId,
    required this.userId,
    required this.status,
    required this.submittedAt,
    this.passApplication,
  });

  factory ClientRegistrationResponse.fromJson(Map<String, dynamic> json) {
    final registration = json['registration'] as Map<String, dynamic>? ?? {};
    return ClientRegistrationResponse(
      registrationId: registration['id'] as String? ?? '',
      userId: registration['user_id'] as String? ?? '',
      status: registration['status'] as String? ?? 'pending',
      submittedAt: parseDate(registration['submitted_at']),
      passApplication: json['pass_application'] != null
          ? PassApplication.fromJson(json['pass_application'] as Map<String, dynamic>)
          : null,
    );
  }

  final String registrationId;
  final String userId;
  final String status;
  final DateTime? submittedAt;
  final PassApplication? passApplication;
}

class ClientProfile {
  ClientProfile({
    required this.userId,
    required this.registrationId,
    required this.status,
    required this.guestPin,
    required this.walletBalance,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ClientProfile.fromJson(Map<String, dynamic> json) {
    return ClientProfile(
      userId: json['user_id'] as String? ?? '',
      registrationId: json['registration_id'] as String? ?? '',
      status: json['status'] as String? ?? 'pending',
      guestPin: json['guest_pin'] as String? ?? '',
      walletBalance: (json['wallet_balance'] as num?)?.toDouble() ?? 0,
      createdAt: parseDate(json['created_at']),
      updatedAt: parseDate(json['updated_at']),
    );
  }

  final String userId;
  final String registrationId;
  final String status;
  final String guestPin;
  final double walletBalance;
  final DateTime? createdAt;
  final DateTime? updatedAt;
}

class ClientWallet {
  ClientWallet({
    required this.userId,
    required this.balance,
    required this.currency,
    required this.lastTopUp,
  });

  factory ClientWallet.fromJson(Map<String, dynamic> json) {
    return ClientWallet(
      userId: json['user_id'] as String? ?? '',
      balance: (json['balance'] as num?)?.toDouble() ?? 0,
      currency: json['currency'] as String? ?? 'MYR',
      lastTopUp: parseDate(json['last_top_up']),
    );
  }

  final String userId;
  final double balance;
  final String currency;
  final DateTime? lastTopUp;
}

class WalletTransaction {
  WalletTransaction({
    required this.id,
    required this.userId,
    required this.amount,
    required this.type,
    required this.description,
    required this.timestamp,
    required this.source,
  });

  factory WalletTransaction.fromJson(Map<String, dynamic> json) {
    return WalletTransaction(
      id: json['id'] as String? ?? '',
      userId: json['user_id'] as String? ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      type: json['type'] as String? ?? 'top_up',
      description: json['description'] as String? ?? '',
      timestamp: parseDate(json['timestamp']),
      source: json['source'] as String? ?? 'card',
    );
  }

  final String id;
  final String userId;
  final double amount;
  final String type;
  final String description;
  final DateTime? timestamp;
  final String source;
}

class WalletActivity {
  WalletActivity({
    required this.wallet,
    required this.transactions,
  });

  factory WalletActivity.fromJson(Map<String, dynamic> json) {
    final transactions = (json['transactions'] as List<dynamic>? ?? [])
        .map((e) => WalletTransaction.fromJson(e as Map<String, dynamic>))
        .toList();
    return WalletActivity(
      wallet: ClientWallet.fromJson(json['wallet'] as Map<String, dynamic>? ?? {}),
      transactions: transactions,
    );
  }

  final ClientWallet wallet;
  final List<WalletTransaction> transactions;
}

class RoleUpgradeRequest {
  RoleUpgradeRequest({
    required this.id,
    required this.userId,
    required this.targetRole,
    required this.reason,
    required this.status,
    required this.submittedAt,
    this.reviewedAt,
    this.reviewerId,
  });

  factory RoleUpgradeRequest.fromJson(Map<String, dynamic> json) {
    return RoleUpgradeRequest(
      id: json['id'] as String? ?? '',
      userId: json['user_id'] as String? ?? '',
      targetRole: json['target_role'] as String? ?? 'guest',
      reason: json['reason'] as String? ?? '',
      status: json['status'] as String? ?? 'pending',
      submittedAt: parseDate(json['submitted_at']),
      reviewedAt: parseDate(json['reviewed_at']),
      reviewerId: json['reviewer_id'] as String?,
    );
  }

  final String id;
  final String userId;
  final String targetRole;
  final String reason;
  final String status;
  final DateTime? submittedAt;
  final DateTime? reviewedAt;
   final String? reviewerId;
}

class Vehicle {
  Vehicle({
    required this.id,
    required this.plate,
  });

  factory Vehicle.fromJson(Map<String, dynamic> json) {
    return Vehicle(
      id: json['id'] as String? ?? '',
      plate: json['plate_text'] as String? ?? '',
    );
  }

  final String id;
  final String plate;
}

class ParkingPass {
  ParkingPass({
    required this.id,
    required this.role,
    required this.planType,
    required this.validFrom,
    required this.validTo,
    required this.priceRm,
    required this.isPaid,
    this.paidAt,
  });

  factory ParkingPass.fromJson(Map<String, dynamic> json) {
    return ParkingPass(
      id: json['id'] as String? ?? '',
      role: json['role'] as String? ?? 'guest',
      planType: json['plan_type'] as String? ?? 'long_semester',
      validFrom: parseDate(json['valid_from']),
      validTo: parseDate(json['valid_to']),
      priceRm: (json['price_rm'] as num?)?.toDouble() ?? 0,
      isPaid: json['is_paid'] as bool? ?? false,
      paidAt: parseDate(json['paid_at']),
    );
  }

  final String id;
  final String role;
  final String planType;
  final DateTime? validFrom;
  final DateTime? validTo;
  final double priceRm;
  final bool isPaid;
  final DateTime? paidAt;
}

class PassApplication {
  PassApplication({
    required this.id,
    required this.userId,
    required this.role,
    required this.planType,
    required this.vehicles,
    required this.status,
    this.reviewerId,
    this.reviewNote,
    this.submittedAt,
    this.reviewedAt,
  });

  factory PassApplication.fromJson(Map<String, dynamic> json) {
    final vehicles = (json['vehicles'] as List<dynamic>? ?? [])
        .map((value) => value.toString())
        .toList();
    return PassApplication(
      id: json['id'] as String? ?? '',
      userId: json['user_id'] as String? ?? '',
      role: json['role'] as String? ?? 'student',
      planType: json['plan_type'] as String? ?? 'long_semester',
      vehicles: vehicles,
      status: json['status'] as String? ?? 'pending',
      reviewerId: json['reviewer_id'] as String?,
      reviewNote: json['review_note'] as String?,
      submittedAt: parseDate(json['submitted_at']),
      reviewedAt: parseDate(json['reviewed_at']),
    );
  }

  final String id;
  final String userId;
  final String role;
  final String planType;
  final List<String> vehicles;
  final String status;
  final String? reviewerId;
  final String? reviewNote;
  final DateTime? submittedAt;
  final DateTime? reviewedAt;
}

class ClientUser {
  ClientUser({
    required this.id,
    required this.name,
    required this.email,
    required this.phone,
    required this.role,
    required this.programme,
  });

  factory ClientUser.fromJson(Map<String, dynamic> json) {
    return ClientUser(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      email: json['email'] as String? ?? '',
      phone: json['phone'] as String? ?? '',
      role: json['role'] as String? ?? 'guest',
      programme: json['programme'] as String? ?? '',
    );
  }

  final String id;
  final String name;
  final String email;
  final String phone;
  final String role;
  final String programme;
}

class GuestSession {
  GuestSession({
    required this.id,
    required this.plateText,
    required this.status,
    required this.startTime,
    this.endTime,
    this.minutes,
    this.fee,
  });

  factory GuestSession.fromJson(Map<String, dynamic> json) {
    return GuestSession(
      id: json['id'] as String? ?? '',
      plateText: json['plate_text'] as String? ?? '',
      status: json['status'] as String? ?? 'open',
      startTime: parseDate(json['start_time']),
      endTime: parseDate(json['end_time']),
      minutes: json['minutes'] as int?,
      fee: (json['fee'] as num?)?.toDouble(),
    );
  }

  final String id;
  final String plateText;
  final String status;
  final DateTime? startTime;
  final DateTime? endTime;
  final int? minutes;
  final double? fee;
}

class ClientSummary {
  ClientSummary({
    required this.user,
    required this.profile,
    required this.vehicles,
    required this.wallet,
    required this.guestSessions,
    required this.roleUpgrades,
    this.passInfo,
    this.passApplications = const [],
  });

  factory ClientSummary.fromJson(Map<String, dynamic> json) {
    final vehicles = (json['vehicles'] as List<dynamic>? ?? [])
        .map((e) => Vehicle.fromJson(e as Map<String, dynamic>))
        .toList();
    final sessions = (json['guest_sessions'] as List<dynamic>? ?? [])
        .map((e) => GuestSession.fromJson(e as Map<String, dynamic>))
        .toList();
    final upgrades = (json['role_upgrades'] as List<dynamic>? ?? [])
        .map((e) => RoleUpgradeRequest.fromJson(e as Map<String, dynamic>))
        .toList();
    final applications = (json['pass_applications'] as List<dynamic>? ?? [])
        .map((e) => PassApplication.fromJson(e as Map<String, dynamic>))
        .toList();
    return ClientSummary(
      user: ClientUser.fromJson(json['user'] as Map<String, dynamic>? ?? {}),
      profile: ClientProfile.fromJson(json['profile'] as Map<String, dynamic>? ?? {}),
      vehicles: vehicles,
      wallet: ClientWallet.fromJson(json['wallet'] as Map<String, dynamic>? ?? {}),
      guestSessions: sessions,
      roleUpgrades: upgrades,
      passInfo: json['pass_info'] != null ? ParkingPass.fromJson(json['pass_info'] as Map<String, dynamic>) : null,
      passApplications: applications,
    );
  }

  final ClientUser user;
  final ClientProfile profile;
  final List<Vehicle> vehicles;
  final ClientWallet wallet;
  final List<GuestSession> guestSessions;
  final List<RoleUpgradeRequest> roleUpgrades;
  final ParkingPass? passInfo;
  final List<PassApplication> passApplications;
}

class GuestLookupResponse {
  GuestLookupResponse({
    required this.session,
    required this.amountDue,
  });

  factory GuestLookupResponse.fromJson(Map<String, dynamic> json) {
    return GuestLookupResponse(
      session: GuestSession.fromJson(json['session'] as Map<String, dynamic>? ?? {}),
      amountDue: (json['amount_due'] as num?)?.toDouble() ?? 0,
    );
  }

  final GuestSession session;
  final double amountDue;
}

class Payment {
  Payment({
    required this.id,
    required this.amount,
    required this.status,
    required this.processor,
    required this.currency,
    required this.timestamp,
    this.sessionId,
    this.passId,
    this.reference,
  });

  factory Payment.fromJson(Map<String, dynamic> json) {
    return Payment(
      id: json['id'] as String? ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      status: json['status'] as String? ?? 'pending',
      processor: json['processor'] as String? ?? 'touchngo',
      currency: json['currency'] as String? ?? 'MYR',
      timestamp: parseDate(json['timestamp']),
      sessionId: json['session_id'] as String?,
      passId: json['pass_id'] as String?,
      reference: json['reference'] as String?,
    );
  }

  final String id;
  final double amount;
  final String status;
  final String processor;
  final String currency;
  final DateTime? timestamp;
  final String? sessionId;
  final String? passId;
  final String? reference;
}

class ParkingVenue {
  ParkingVenue({
    required this.id,
    required this.name,
    required this.capacity,
    required this.occupied,
    required this.percent,
  });

  factory ParkingVenue.fromJson(Map<String, dynamic> json) {
    return ParkingVenue(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      capacity: json['capacity'] as int? ?? 0,
      occupied: json['occupied'] as int? ?? 0,
      percent: (json['percent'] as num?)?.toDouble() ?? 0,
    );
  }

  final String id;
  final String name;
  final int capacity;
  final int occupied;
  final double percent;
}

class ParkingOverview {
  ParkingOverview(this.venues);

  factory ParkingOverview.fromJson(Map<String, dynamic> json) {
    final venues = (json['venues'] as List<dynamic>? ?? [])
        .map((e) => ParkingVenue.fromJson(e as Map<String, dynamic>))
        .toList();
    return ParkingOverview(venues);
  }

  final List<ParkingVenue> venues;
}

class AuthResponse {
  AuthResponse({
    required this.token,
    required this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      token: json['token'] as String? ?? '',
      user: ClientUser.fromJson(json['user'] as Map<String, dynamic>? ?? {}),
    );
  }

  final String token;
  final ClientUser user;
}

class AppNotification {
  AppNotification({
    required this.id,
    required this.userId,
    required this.message,
    required this.createdAt,
    required this.isRead,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as String? ?? '',
      userId: json['user_id'] as String? ?? '',
      message: json['message'] as String? ?? '',
      createdAt: parseDate(json['created_at']),
      isRead: json['is_read'] as bool? ?? false,
    );
  }

  final String id;
  final String userId;
  final String message;
  final DateTime? createdAt;
  final bool isRead;
}

class PortalSignupPayload {
  PortalSignupPayload({
    required this.name,
    required this.email,
    required this.phone,
    required this.programme,
    required this.password,
  });

  Map<String, dynamic> toJson() => {
        'name': name,
        'email': email,
        'phone': phone,
        'programme': programme,
        'password': password,
      };

  final String name;
  final String email;
  final String phone;
  final String programme;
  final String password;
}
