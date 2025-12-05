import 'package:flutter/foundation.dart';

import '../models/models.dart';
import '../services/api_service.dart';

class ClientState extends ChangeNotifier {
  ClientState({ClientApiService? api})
      : api = api ?? ClientApiService(),
        activeUserId = const String.fromEnvironment('SMARTGATE_DEMO_USER', defaultValue: '');

  final ClientApiService api;

  bool isBusy = false;
  String? errorMessage;
  String? authToken;

  ClientRegistrationResponse? lastRegistration;
  ClientSummary? summary;
  WalletActivity? walletActivity;
  GuestLookupResponse? guestLookup;
  Payment? lastPayment;
  ParkingOverview? parking;
  RoleUpgradeRequest? lastUpgrade;
  List<AppNotification> notifications = [];

  String activeUserId;

  bool get hasActiveUser => activeUserId.isNotEmpty;
  bool get isAuthenticated => authToken != null && authToken!.isNotEmpty && hasActiveUser;

  Future<void> registerClient(ClientRegistrationPayload payload) async {
    await _run(() async {
      lastRegistration = await api.register(payload);
      if (lastRegistration != null) {
        activeUserId = lastRegistration!.userId;
        await _hydrateUser();
      }
    });
  }

  Future<void> signupAccount(PortalSignupPayload payload) async {
    await _run(() async {
      final response = await api.signupPortal(payload);
      _setAuth(response);
      await _hydrateUser();
    });
  }

  Future<void> loginAccount({required String identifier, required String password}) async {
    await _run(() async {
      final response = await api.loginPortal(identifier: identifier, password: password);
      _setAuth(response);
      await _hydrateUser();
    });
  }

  void logout() {
    authToken = null;
    activeUserId = '';
    summary = null;
    walletActivity = null;
    guestLookup = null;
    lastPayment = null;
    notifications = [];
    api.setToken(null);
    notifyListeners();
  }

  Future<void> selectUser(String userId) async {
    if (userId.isEmpty) return;
    activeUserId = userId;
    await _run(() async {
      await _hydrateUser();
    });
  }

  Future<void> refreshWallet() async {
    if (!hasActiveUser) return;
    await _run(() async {
      walletActivity = await api.fetchWallet(activeUserId);
      summary = summary?.copyWithWallet(walletActivity!.wallet);
    }, silent: true);
  }

  Future<void> topUp(double amount) async {
    if (!hasActiveUser) return;
    await _run(() async {
      walletActivity = await api.topUpWallet(activeUserId, amount);
      summary = summary?.copyWithWallet(walletActivity!.wallet);
    });
  }

  Future<void> submitUpgrade(String targetRole, String reason) async {
    if (!hasActiveUser) return;
    await _run(() async {
      lastUpgrade = await api.submitRoleUpgrade(activeUserId, targetRole, reason);
      await _hydrateUser();
    });
  }

  Future<void> lookupGuest({String? sessionId, String? plateText}) async {
    await _run(() async {
      guestLookup = await api.lookupGuestSession(sessionId: sessionId, plateText: plateText);
    }, silent: true);
  }

  Future<void> payGuest({required String paymentSource}) async {
    if (guestLookup == null) return;
    await _run(() async {
      lastPayment = await api.payGuestSession(
        sessionId: guestLookup!.session.id,
        amount: guestLookup!.amountDue,
        paymentSource: paymentSource,
        userId: paymentSource == 'wallet' ? activeUserId : null,
      );
      guestLookup = null;
      await refreshWallet();
    });
  }

  Future<void> payPassInvoice() async {
    if (!hasActiveUser || summary?.passInfo == null) return;
    await _run(() async {
      await api.payPassInvoice(summary!.passInfo!.id, activeUserId);
      await _hydrateUser();
    });
  }

  Future<void> refreshParking() async {
    await _run(() async {
      parking = await api.fetchParkingOverview();
    }, silent: true);
  }

  Future<void> refreshNotifications() async {
    if (!hasActiveUser) return;
    notifications = await api.fetchNotifications(activeUserId);
    notifyListeners();
  }

  Future<void> markNotificationRead(String notificationId) async {
    if (!hasActiveUser) return;
    final updated = await api.acknowledgeNotification(activeUserId, notificationId);
    notifications = notifications
        .map((note) => note.id == updated.id ? updated : note)
        .toList();
    notifyListeners();
  }

  Future<void> _hydrateUser() async {
    if (!hasActiveUser) return;
    summary = await api.fetchSummary(activeUserId);
    walletActivity = await api.fetchWallet(activeUserId);
    parking ??= await api.fetchParkingOverview();
    await refreshNotifications();
  }

  Future<void> _run(Future<void> Function() task, {bool silent = false}) async {
    if (!silent) {
      isBusy = true;
      errorMessage = null;
      notifyListeners();
    }
    try {
      await task();
    } catch (err) {
      errorMessage = err.toString();
    } finally {
      isBusy = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    api.dispose();
    super.dispose();
  }

  void _setAuth(AuthResponse response) {
    authToken = response.token;
    api.setToken(authToken);
    activeUserId = response.user.id;
    summary = null;
    walletActivity = null;
    notifications = [];
    notifyListeners();
  }
}

extension on ClientSummary {
  ClientSummary copyWithWallet(ClientWallet wallet) {
    return ClientSummary(
      user: user,
      profile: profile,
      vehicles: vehicles,
      wallet: wallet,
      guestSessions: guestSessions,
      roleUpgrades: roleUpgrades,
      passInfo: passInfo,
      passApplications: passApplications,
    );
  }
}
