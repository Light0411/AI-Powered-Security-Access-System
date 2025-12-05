import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../models/models.dart';
import '../state/client_state.dart';

const _detailSeparator = ' \u2022 ';

class SelfServiceScreen extends StatefulWidget {
  const SelfServiceScreen({super.key});

  @override
  State<SelfServiceScreen> createState() => _SelfServiceScreenState();
}

class _SelfServiceScreenState extends State<SelfServiceScreen> {
  final _topUpController = TextEditingController(text: '20');
  final _upgradeReason = TextEditingController();
  String _targetRole = 'staff';
  bool _walletExpanded = false;
  bool _upgradeExpanded = false;

  @override
  Widget build(BuildContext context) {
    final state = context.watch<ClientState>();
    final summary = state.summary;
    if (!state.isAuthenticated) {
      return const Center(
        child: Text('Sign in to view your portal.'),
      );
    }
    if (summary == null) {
      return const Center(child: CircularProgressIndicator());
    }
    return RefreshIndicator(
      onRefresh: () async => state.selectUser(state.activeUserId),
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (state.errorMessage != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.redAccent.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.redAccent.withOpacity(0.4)),
                  ),
                  child: Text(
                    state.errorMessage!,
                    style: const TextStyle(color: Colors.redAccent),
                  ),
                ),
              ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Welcome back', style: Theme.of(context).textTheme.labelMedium),
                    Text(summary.user.name, style: Theme.of(context).textTheme.headlineSmall),
                    Text(summary.user.email, style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
                TextButton(onPressed: state.logout, child: const Text('Logout')),
              ],
            ),
            const SizedBox(height: 16),
            _SummaryCard(
              summary: summary,
              latestApplication: summary.passApplications.isNotEmpty
                  ? summary.passApplications.first
                  : state.lastRegistration?.passApplication,
              onPayPass: state.isBusy ? null : state.payPassInvoice,
              isPaying: state.isBusy,
            ),
            const SizedBox(height: 16),
            _WalletCard(
              wallet: state.walletActivity,
              onTopUp: (amount) => state.topUp(amount),
              topUpController: _topUpController,
              isExpanded: _walletExpanded,
              onToggle: () => setState(() => _walletExpanded = !_walletExpanded),
            ),
            const SizedBox(height: 16),
            _UpgradeCard(
              targetRole: _targetRole,
              onRoleChanged: (role) => setState(() => _targetRole = role),
              upgradeReason: _upgradeReason,
              onSubmit: () => state.submitUpgrade(_targetRole, _upgradeReason.text.trim()),
              lastUpgrade: state.lastUpgrade,
              isExpanded: _upgradeExpanded,
              onToggle: () => setState(() => _upgradeExpanded = !_upgradeExpanded),
            ),
            const SizedBox(height: 16),
            _GuestHistory(sessions: summary.guestSessions),
          ],
        ),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({
    required this.summary,
    required this.onPayPass,
    required this.isPaying,
    this.latestApplication,
  });

  final ClientSummary summary;
  final PassApplication? latestApplication;
  final VoidCallback? onPayPass;
  final bool isPaying;

  @override
  Widget build(BuildContext context) {
    final pass = summary.passInfo;
    final application = latestApplication;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(summary.user.name, style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 4),
                      Text(
                        '${summary.user.programme}$_detailSeparator${summary.user.role.toUpperCase()}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 220),
                  child: Align(
                    alignment: Alignment.topRight,
                    child: pass != null
                        ? _PassSummary(pass: pass)
                        : Text(
                            'No active pass',
                            style: Theme.of(context).textTheme.bodySmall,
                            textAlign: TextAlign.right,
                          ),
                  ),
                ),
              ],
            ),
            if (application != null) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.02),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: _statusColor(application.status).withOpacity(0.4)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Application status',
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(color: Colors.white70),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      application.status.toUpperCase(),
                      style: TextStyle(
                        color: _statusColor(application.status),
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'Submitted ${formatDisplayDate(application.submittedAt)}',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.white60),
                    ),
                    if (application.reviewNote != null && application.reviewNote!.isNotEmpty)
                      Text(
                        'Note: ${application.reviewNote}',
                        style: const TextStyle(color: Colors.white60, fontSize: 12),
                      ),
                    const SizedBox(height: 6),
                    Text(
                      _statusMessage(application, pass),
                      style: TextStyle(
                        color: _statusColor(application.status),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
            if (pass != null && !pass.isPaid) ...[
              const SizedBox(height: 12),
              FilledButton(
                onPressed: isPaying ? null : onPayPass,
                child: Text(isPaying ? 'Processing…' : 'Pay from Wallet'),
              ),
            ],
            Wrap(
              spacing: 8,
              children: summary.vehicles.map((vehicle) => Chip(label: Text(vehicle.plate))).toList(),
            ),
          ],
        ),
      ),
    );
  }

  static Color _statusColor(String status) {
    switch (status) {
      case 'approved':
        return Colors.greenAccent;
      case 'rejected':
        return Colors.redAccent;
      default:
        return Colors.amberAccent;
    }
  }

  static String _statusMessage(PassApplication application, ParkingPass? pass) {
    switch (application.status) {
      case 'approved':
        if (pass != null && pass.isPaid) {
          return 'Approved and paid. LPR will honor your pass.';
        }
        return 'Approved. Pay the wallet invoice to activate access.';
      case 'rejected':
        return 'Rejected. Update your details and reapply.';
      default:
        return 'Pending admin approval.';
    }
  }
}


String _planLabel(String planType) {
  switch (planType) {
    case 'short_semester':
      return 'Short Semester';
    case 'long_semester':
      return 'Long Semester';
    case 'annual':
      return 'Annual';
    default:
      return planType;
  }
}

class _WalletCard extends StatelessWidget {
  const _WalletCard({
    required this.wallet,
    required this.onTopUp,
    required this.topUpController,
    required this.isExpanded,
    required this.onToggle,
  });

  final WalletActivity? wallet;
  final TextEditingController topUpController;
  final void Function(double amount) onTopUp;
  final bool isExpanded;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    final balance = wallet?.wallet.balance ?? 0;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Wallet balance', style: Theme.of(context).textTheme.titleLarge),
                IconButton(
                  onPressed: onToggle,
                  icon: Icon(isExpanded ? Icons.expand_less : Icons.expand_more),
                  tooltip: isExpanded ? 'Collapse wallet' : 'Expand wallet',
                ),
              ],
            ),
            Text('RM${balance.toStringAsFixed(2)}', style: Theme.of(context).textTheme.displaySmall),
            AnimatedCrossFade(
              firstChild: const SizedBox.shrink(),
              secondChild: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: topUpController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'Top-up amount'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      FilledButton(
                        onPressed: () {
                          final amount = double.tryParse(topUpController.text.trim());
                          if (amount != null && amount > 0) {
                            onTopUp(amount);
                          }
                        },
                        child: const Text('Add funds'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text('Recent activity', style: Theme.of(context).textTheme.titleSmall),
                  ...?wallet?.transactions.take(5).map(
                        (txn) => ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(txn.description),
                          subtitle: Text(formatDisplayDate(txn.timestamp)),
                          trailing: Text(
                            txn.amount >= 0
                                ? '+RM${txn.amount.toStringAsFixed(2)}'
                                : '-RM${txn.amount.abs().toStringAsFixed(2)}',
                            style: TextStyle(color: txn.amount >= 0 ? Colors.green : Colors.redAccent),
                          ),
                        ),
                      ),
                ],
              ),
              crossFadeState: isExpanded ? CrossFadeState.showSecond : CrossFadeState.showFirst,
              duration: const Duration(milliseconds: 200),
              alignment: Alignment.topCenter,
            ),
          ],
        ),
      ),
    );
  }
}

class _UpgradeCard extends StatelessWidget {
  const _UpgradeCard({
    required this.targetRole,
    required this.onRoleChanged,
    required this.upgradeReason,
    required this.onSubmit,
    required this.lastUpgrade,
    required this.isExpanded,
    required this.onToggle,
  });

  final String targetRole;
  final ValueChanged<String> onRoleChanged;
  final TextEditingController upgradeReason;
  final VoidCallback onSubmit;
  final RoleUpgradeRequest? lastUpgrade;
  final bool isExpanded;
  final VoidCallback onToggle;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Role upgrade', style: Theme.of(context).textTheme.titleMedium),
                IconButton(
                  onPressed: onToggle,
                  icon: Icon(isExpanded ? Icons.expand_less : Icons.expand_more),
                  tooltip: isExpanded ? 'Collapse role upgrade' : 'Expand role upgrade',
                ),
              ],
            ),
            if (lastUpgrade != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text('Request ${lastUpgrade!.id} is ${lastUpgrade!.status}.'),
              ),
            AnimatedCrossFade(
              firstChild: const SizedBox.shrink(),
              secondChild: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  DropdownButtonFormField<String>(
                    value: targetRole,
                    decoration: const InputDecoration(labelText: 'Target role'),
                    items: const [
                      DropdownMenuItem(value: 'staff', child: Text('Staff')),
                      DropdownMenuItem(value: 'security', child: Text('Security')),
                    ],
                    onChanged: (value) => onRoleChanged(value ?? targetRole),
                  ),
                  TextField(
                    controller: upgradeReason,
                    minLines: 2,
                    maxLines: 4,
                    decoration: const InputDecoration(labelText: 'Reason'),
                  ),
                  const SizedBox(height: 12),
                  FilledButton(onPressed: onSubmit, child: const Text('Submit request')),
                ],
              ),
              crossFadeState: isExpanded ? CrossFadeState.showSecond : CrossFadeState.showFirst,
              duration: const Duration(milliseconds: 200),
              alignment: Alignment.topCenter,
            ),
          ],
        ),
      ),
    );
  }
}

class _PassSummary extends StatelessWidget {
  const _PassSummary({required this.pass});

  final ParkingPass pass;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(_planLabel(pass.planType), style: textTheme.labelMedium),
        const SizedBox(height: 4),
        Text('RM${pass.priceRm.toStringAsFixed(2)}', style: textTheme.bodyMedium),
        const SizedBox(height: 4),
        Text(
          '${formatDisplayDate(pass.validFrom)}$_detailSeparator${formatDisplayDate(pass.validTo)}',
          style: textTheme.bodySmall,
          textAlign: TextAlign.right,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: 4),
        Text(
          pass.isPaid ? 'Paid' : 'Awaiting payment',
          style: textTheme.bodySmall?.copyWith(
            color: pass.isPaid ? Colors.greenAccent : Colors.amberAccent,
          ),
        ),
      ],
    );
  }
}

class _GuestHistory extends StatelessWidget {
  const _GuestHistory({required this.sessions});

  final List<GuestSession> sessions;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Recent guest sessions', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (sessions.isEmpty)
              const Text('No guest visits yet.')
            else
              ...sessions.take(5).map(
                (session) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(session.plateText),
                  subtitle: Text('${session.status}$_detailSeparator${formatDisplayDate(session.startTime)}$_detailSeparator${session.id}'),
                  trailing: Wrap(
                    spacing: 4,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      Text(
                        'RM${(session.fee ?? 0).toStringAsFixed(2)}',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      IconButton(
                        tooltip: 'Copy session ID',
                        icon: const Icon(Icons.copy, size: 18),
                        onPressed: () => Clipboard.setData(ClipboardData(text: session.id)),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

