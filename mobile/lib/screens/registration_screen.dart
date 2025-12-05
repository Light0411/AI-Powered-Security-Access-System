import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/models.dart';
import '../state/client_state.dart';
import '../widgets/ui_kit.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _programme = TextEditingController();
  final _vehicle = TextEditingController();

  String role = 'student';
  String planType = 'long_semester';
  String? _formError;
  bool _prefilled = false;
  bool _formExpanded = false;
  bool _notificationsExpanded = true;

  final vehicles = <String>[];

  static const _planOptions = [
    {'type': 'short_semester', 'label': 'Short Semester', 'duration': '50 days', 'price': 'RM30'},
    {'type': 'long_semester', 'label': 'Long Semester', 'duration': '100 days', 'price': 'RM50'},
    {'type': 'annual', 'label': 'Full Year', 'duration': '365 days', 'price': 'RM120'},
  ];

  @override
  Widget build(BuildContext context) {
    final state = context.watch<ClientState>();
    _maybePrefill(state);
    final summary = state.summary;
    final hasProfile = summary?.user != null;
    final latestApplication = (summary?.passApplications.isNotEmpty ?? false)
        ? summary!.passApplications.first
        : state.lastRegistration?.passApplication;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'REGISTRATION',
            style: TextStyle(
              fontSize: 10,
              color: AppColors.textGrey,
              letterSpacing: 2,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          if (latestApplication != null) ...[
            _ApplicationStatusBanner(application: latestApplication),
            const SizedBox(height: 16),
          ],
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Expanded(
                      child: Text(
                        'Apply for Pass',
                        style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                      ),
                    ),
                    IconButton(
                      onPressed: () => setState(() => _formExpanded = !_formExpanded),
                      icon: Icon(_formExpanded ? Icons.expand_less : Icons.expand_more),
                      tooltip: _formExpanded ? 'Collapse form' : 'Expand form',
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                AnimatedCrossFade(
                  alignment: Alignment.topCenter,
                  duration: const Duration(milliseconds: 250),
                  sizeCurve: Curves.easeInOut,
                  firstChild: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    child: Text(
                      'Expand to submit a new application.',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                  secondChild: Form(
                    key: _formKey,
                    child: Column(
                      children: [
                        GlassTextField(controller: _name, label: 'Full Name', readOnly: hasProfile),
                        const SizedBox(height: 12),
                        GlassTextField(
                          controller: _email,
                          label: 'Email',
                          readOnly: hasProfile,
                          keyboardType: TextInputType.emailAddress,
                        ),
                        const SizedBox(height: 12),
                        GlassTextField(
                          controller: _phone,
                          label: 'Phone',
                          readOnly: hasProfile,
                          keyboardType: TextInputType.phone,
                        ),
                        const SizedBox(height: 12),
                        GlassTextField(controller: _programme, label: 'Programme', readOnly: hasProfile),
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          decoration: BoxDecoration(
                            color: AppColors.cardBg.withOpacity(0.85),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: Colors.white.withOpacity(0.08)),
                          ),
                          child: DropdownButtonHideUnderline(
                            child: DropdownButton<String>(
                              value: role,
                              dropdownColor: AppColors.cardBg,
                              isExpanded: true,
                              style: const TextStyle(color: Colors.white),
                              items: const [
                                DropdownMenuItem(value: 'student', child: Text('Student')),
                                DropdownMenuItem(value: 'staff', child: Text('Staff')),
                                DropdownMenuItem(value: 'security', child: Text('Security')),
                              ],
                              onChanged: state.isBusy
                                  ? null
                                  : (val) {
                                      if (val != null) {
                                        setState(() => role = val);
                                      }
                                    },
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                            'Select Pass Plan',
                            style: Theme.of(context).textTheme.titleSmall?.copyWith(color: Colors.white),
                          ),
                        ),
                        const SizedBox(height: 12),
                        Column(
                          children: _planOptions
                              .map(
                                (plan) => Padding(
                                  padding: const EdgeInsets.only(bottom: 12),
                                  child: GlassCard(
                                    onTap: state.isBusy
                                        ? null
                                        : () => setState(() {
                                              planType = plan['type']!;
                                            }),
                                    borderColor:
                                        planType == plan['type'] ? AppColors.accentBlue : Colors.white.withOpacity(0.08),
                                    child: Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              plan['label']!,
                                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(plan['duration']!, style: const TextStyle(color: AppColors.textGrey)),
                                          ],
                                        ),
                                        Text(plan['price']!,
                                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                                      ],
                                    ),
                                  ),
                                ),
                              )
                              .toList(),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            Expanded(
                              child: GlassTextField(
                                controller: _vehicle,
                                label: 'Vehicle Plate',
                                keyboardType: TextInputType.text,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              decoration:
                                  BoxDecoration(color: AppColors.accentBlue, borderRadius: BorderRadius.circular(12)),
                              child: IconButton(
                                icon: const Icon(Icons.add, color: Colors.white),
                                onPressed: () {
                                  if (_vehicle.text.isNotEmpty) {
                                    setState(() {
                                      vehicles.add(_vehicle.text.trim().toUpperCase());
                                      _vehicle.clear();
                                    });
                                  }
                                },
                              ),
                            )
                          ],
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          children: vehicles
                              .map(
                                (plate) => Chip(
                                  label: Text(plate),
                                  backgroundColor: AppColors.cardBg,
                                  labelStyle: const TextStyle(color: Colors.white),
                                ),
                              )
                              .toList(),
                        ),
                        const SizedBox(height: 24),
                        SizedBox(
                          width: double.infinity,
                          child: NeonButton(
                            label: 'Submit Application',
                            onPressed: state.isBusy ? null : () => _submit(context),
                          ),
                        ),
                        if (_formError != null) ...[
                          const SizedBox(height: 12),
                          Text(
                            _formError!,
                            style: const TextStyle(color: Colors.redAccent, fontSize: 12),
                          ),
                        ],
                        if (state.errorMessage != null) ...[
                          const SizedBox(height: 12),
                          Text(
                            state.errorMessage!,
                            style: const TextStyle(color: Colors.redAccent, fontSize: 12),
                          ),
                        ],
                      ],
                    ),
                  ),
                  crossFadeState: _formExpanded ? CrossFadeState.showSecond : CrossFadeState.showFirst,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text('Notifications', style: Theme.of(context).textTheme.titleMedium),
                    ),
                    IconButton(
                      onPressed: state.refreshNotifications,
                      icon: const Icon(Icons.refresh, size: 18),
                      tooltip: 'Refresh notifications',
                    ),
                    IconButton(
                      onPressed: () => setState(() => _notificationsExpanded = !_notificationsExpanded),
                      icon: Icon(_notificationsExpanded ? Icons.expand_less : Icons.expand_more),
                      tooltip: _notificationsExpanded ? 'Collapse notifications' : 'Expand notifications',
                    ),
                  ],
                ),
                AnimatedCrossFade(
                  firstChild: _CollapsedNotificationSummary(notifications: state.notifications),
                  secondChild: state.notifications.isEmpty
                      ? const Padding(
                          padding: EdgeInsets.symmetric(vertical: 12),
                          child: Text('No notifications yet.'),
                        )
                      : Column(
                          children: state.notifications.take(5).map(
                            (note) => ListTile(
                              contentPadding: EdgeInsets.zero,
                              title: Text(note.message),
                              subtitle: Text(formatDisplayDate(note.createdAt)),
                              trailing: note.isRead
                                  ? const Icon(Icons.check, color: Colors.green, size: 16)
                                  : TextButton(
                                      onPressed: () => state.markNotificationRead(note.id),
                                      child: const Text('Mark read'),
                                    ),
                            ),
                          ).toList(),
                        ),
                  crossFadeState: _notificationsExpanded ? CrossFadeState.showSecond : CrossFadeState.showFirst,
                  duration: const Duration(milliseconds: 200),
                  alignment: Alignment.topCenter,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _submit(BuildContext context) async {
    if (!_formKey.currentState!.validate()) return;
    if (vehicles.isEmpty && _vehicle.text.isNotEmpty) {
      setState(() => vehicles.add(_vehicle.text.trim().toUpperCase()));
    }
    if (vehicles.isEmpty) {
      setState(() => _formError = 'Add at least one vehicle plate to continue.');
      return;
    }
    setState(() => _formError = null);
    final payload = ClientRegistrationPayload(
      name: _name.text.trim(),
      email: _email.text.trim(),
      phone: _phone.text.trim(),
      programme: _programme.text.trim(),
      role: role,
      planType: planType,
      vehicles: vehicles.toList(),
    );
    await context.read<ClientState>().registerClient(payload);
  }

  void _maybePrefill(ClientState state) {
    if (_prefilled) return;
    final summary = state.summary;
    if (summary == null) return;
    final user = summary.user;
    setState(() {
      _name.text = user.name;
      _email.text = user.email;
      _phone.text = user.phone;
      _programme.text = user.programme;
      role = user.role == 'guest' ? 'student' : user.role;
      vehicles
        ..clear()
        ..addAll(summary.vehicles.map((vehicle) => vehicle.plate.toUpperCase()));
      _prefilled = true;
    });
  }
}

class _ApplicationStatusBanner extends StatelessWidget {
  const _ApplicationStatusBanner({required this.application});

  final PassApplication application;

  @override
  Widget build(BuildContext context) {
    final color = _statusColor();
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Application status',
            style: TextStyle(
              fontSize: 12,
              letterSpacing: 2,
              color: AppColors.textGrey,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                application.status.toUpperCase(),
                style: TextStyle(
                  color: color,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    application.planType.toUpperCase(),
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                  ),
                  Text(
                    'Role ${application.role.toUpperCase()}',
                    style: const TextStyle(color: AppColors.textGrey, fontSize: 12),
                  ),
                ],
              ),
            ],
          ),
          Text(
            'Submitted ${formatDisplayDate(application.submittedAt)}',
            style: const TextStyle(color: AppColors.textGrey, fontSize: 12),
          ),
          if (application.reviewedAt != null)
            Text(
              'Reviewed ${formatDisplayDate(application.reviewedAt)}',
              style: const TextStyle(color: AppColors.textGrey, fontSize: 12),
            ),
          const SizedBox(height: 8),
          Text(
            'Vehicles',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(color: Colors.white),
          ),
          const SizedBox(height: 6),
          if (application.vehicles.isNotEmpty)
            Wrap(
              spacing: 8,
              children: application.vehicles
                  .map(
                    (plate) => Chip(
                      label: Text(plate),
                      backgroundColor: AppColors.cardBg,
                      labelStyle: const TextStyle(color: Colors.white),
                    ),
                  )
                  .toList(),
            )
          else
            const Text(
              'No vehicles submitted',
              style: TextStyle(color: AppColors.textGrey, fontSize: 12),
            ),
          const SizedBox(height: 8),
          Text(
            _statusMessage(),
            style: TextStyle(color: color, fontWeight: FontWeight.w600),
          ),
          if (application.reviewNote != null && application.reviewNote!.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              'Note: ${application.reviewNote}',
              style: const TextStyle(color: AppColors.textGrey, fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }

  Color _statusColor() {
    switch (application.status) {
      case 'approved':
        return Colors.greenAccent;
      case 'rejected':
        return Colors.redAccent;
      default:
        return Colors.amberAccent;
    }
  }

  String _statusMessage() {
    switch (application.status) {
      case 'approved':
        return 'Approved. Pay the wallet invoice to activate your pass.';
      case 'rejected':
        return 'Rejected. Update your details and submit a new application.';
      default:
        return 'Pending admin approval.';
    }
  }
}

class _CollapsedNotificationSummary extends StatelessWidget {
  const _CollapsedNotificationSummary({required this.notifications});

  final List<AppNotification> notifications;

  @override
  Widget build(BuildContext context) {
    final unread = notifications.where((note) => !note.isRead).length;
    final latest = notifications.isNotEmpty ? notifications.first : null;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            unread > 0 ? '$unread unread alert${unread == 1 ? '' : 's'}' : 'All caught up',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          if (latest != null) ...[
            const SizedBox(height: 6),
            Text(
              latest.message,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.white70),
            ),
            Text(
              formatDisplayDate(latest.createdAt),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.white38),
            ),
          ],
        ],
      ),
    );
  }
}
