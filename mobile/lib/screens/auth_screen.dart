import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../state/client_state.dart';
import '../widgets/ui_kit.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool showLogin = true;
  final _identifier = TextEditingController();
  final _password = TextEditingController();

  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _programme = TextEditingController();

  @override
  Widget build(BuildContext context) {
    final state = context.watch<ClientState>();

    return ParkFlowScaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _logo(),
              const SizedBox(height: 24),

              const Text(
                'SmartGate',
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  letterSpacing: -1,
                ),
              ),
              const Text(
                'SECURE ACCESS PORTAL',
                style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textGrey,
                  letterSpacing: 2,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 48),

              GlassCard(
                child: Column(
                  children: [
                    _tabSwitcher(),
                    const SizedBox(height: 24),

                    showLogin ? _loginForm(state) : _signupForm(state),

                    if (state.errorMessage != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 16),
                        child: Text(
                          state.errorMessage!,
                          style: const TextStyle(
                              color: Colors.redAccent, fontSize: 12),
                          textAlign: TextAlign.center,
                        ),
                      )
                  ],
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _logo() {
    return Container(
      width: 80,
      height: 80,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          colors: [AppColors.accentBlue, AppColors.accentCyan],
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.accentBlue.withOpacity(0.5),
            blurRadius: 30,
          )
        ],
      ),
      child: const Icon(Icons.sensor_occupied_rounded,
          size: 40, color: Colors.white),
    );
  }

  Widget _tabSwitcher() {
    return Container(
      height: 48,
      decoration: BoxDecoration(
        color: Colors.black26,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          _buildTab('Login', showLogin, () => setState(() => showLogin = true)),
          _buildTab('Sign Up', !showLogin, () => setState(() => showLogin = false)),
        ],
      ),
    );
  }

  Widget _loginForm(ClientState state) {
    return Column(
      children: [
        GlassInput(
          controller: _identifier,
          label: 'Email or ID',
          icon: Icons.person,
        ),
        const SizedBox(height: 16),
        GlassInput(
          controller: _password,
          label: 'Password',
          icon: Icons.lock_outline,
          obscure: true,
        ),
        const SizedBox(height: 24),
        SizedBox(
          width: double.infinity,
          child: NeonButton(
            label: "CONNECT",
            onPressed: state.isBusy
                ? null
                : () => state.loginAccount(
                      identifier: _identifier.text,
                      password: _password.text,
                    ),
          ),
        ),
      ],
    );
  }

  Widget _signupForm(ClientState state) {
    return Column(
      children: [
        GlassInput(controller: _name, label: 'Full Name', icon: Icons.badge),
        const SizedBox(height: 12),
        GlassInput(controller: _email, label: 'Email', icon: Icons.email),
        const SizedBox(height: 12),
        GlassInput(controller: _phone, label: 'Phone', icon: Icons.phone),
        const SizedBox(height: 12),
        GlassInput(controller: _programme, label: 'Programme', icon: Icons.school),
        const SizedBox(height: 12),
        GlassInput(controller: _password, label: 'Password', icon: Icons.lock, obscure: true),
        const SizedBox(height: 24),
        SizedBox(
          width: double.infinity,
          child: NeonButton(
            label: "REGISTER",
            color: AppColors.accentBlue,
            onPressed: state.isBusy
                ? null
                : () => state.signupAccount(
                      PortalSignupPayload(
                        name: _name.text,
                        email: _email.text,
                        phone: _phone.text,
                        programme: _programme.text,
                        password: _password.text,
                      ),
                    ),
          ),
        ),
      ],
    );
  }

  Widget _buildTab(String text, bool active, VoidCallback onTap) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: active ? Colors.white.withOpacity(0.1) : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            text,
            style: TextStyle(
              color: active ? Colors.white : Colors.white38,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }
}
