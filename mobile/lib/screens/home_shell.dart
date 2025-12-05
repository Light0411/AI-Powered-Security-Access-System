import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../state/client_state.dart';
import '../widgets/ui_kit.dart';
import 'guest_payment_screen.dart';
import 'parking_panel_screen.dart';
import 'registration_screen.dart';
import 'self_service_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 1; // Default to Portal

  final List<Widget> _screens = [
    const RegistrationScreen(),
    const SelfServiceScreen(),
    const GuestPaymentScreen(),
    const ParkingPanelScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return ParkFlowScaffold(
      // The body just renders the current screen
      // IMPORTANT: The screens themselves should NOT have a Scaffold, just ListView/Column
      body: _screens[_index],
      
      // Floating Glass Bottom Bar
      bottomNavigationBar: Container(
        margin: const EdgeInsets.all(20),
        height: 70,
        decoration: BoxDecoration(
          color: const Color(0xFF0F172A).withOpacity(0.8),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.white.withOpacity(0.1)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.3),
              blurRadius: 20,
              offset: const Offset(0, 10),
            )
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _NavBarIcon(Icons.badge, 0, _index, () => setState(() => _index = 0)),
                _NavBarIcon(Icons.dashboard, 1, _index, () => setState(() => _index = 1)),
                _NavBarIcon(Icons.qr_code_scanner, 2, _index, () => setState(() => _index = 2)),
                _NavBarIcon(Icons.local_parking, 3, _index, () => setState(() => _index = 3)),
                IconButton(
                  icon: const Icon(Icons.logout, color: Colors.redAccent),
                  onPressed: () => context.read<ClientState>().logout(),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NavBarIcon extends StatelessWidget {
  final IconData icon;
  final int index;
  final int currentIndex;
  final VoidCallback onTap;

  const _NavBarIcon(this.icon, this.index, this.currentIndex, this.onTap);

  @override
  Widget build(BuildContext context) {
    final isSelected = index == currentIndex;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.accentGreen.withOpacity(0.2) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(
          icon,
          color: isSelected ? AppColors.accentGreen : Colors.white54,
          size: 26,
        ),
      ),
    );
  }
}