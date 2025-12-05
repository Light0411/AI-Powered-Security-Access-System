import 'dart:ui';
import 'package:flutter/material.dart';

/// ------------------------------------------------------------
/// COLORS
/// ------------------------------------------------------------
class AppColors {
  static const bgDark = Color(0xFF010409);
  static const bgDarker = Color(0xFF0D1117);

  static const bgLight = Color(0xFF161B22);

  static const cardBg = Color(0xFF161B22);

  static const accentGreen = Color(0xFF2EA043);
  static const accentBlue = Color(0xFF1F6FEB);
  static const accentCyan = Color(0xFF39C5CF);
  static const accentPurple = Color(0xFF8250DF);

  static const textGrey = Color(0xFF8B949E);
  static const textWhite = Colors.white;
}

/// ------------------------------------------------------------
/// PARKFLOW SCAFFOLD
/// ------------------------------------------------------------
class ParkFlowScaffold extends StatefulWidget {
  final Widget body;
  final Widget? bottomNavigationBar;

  const ParkFlowScaffold({super.key, required this.body, this.bottomNavigationBar});

  @override
  State<ParkFlowScaffold> createState() => _ParkFlowScaffoldState();
}

class _ParkFlowScaffoldState extends State<ParkFlowScaffold>
    with SingleTickerProviderStateMixin {
  late final AnimationController _bg;

  @override
  void initState() {
    super.initState();
    _bg = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 14),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _bg.dispose();
    super.dispose();
  }

  Widget _buildAnimatedBackground() {
    return Positioned.fill(
      child: AnimatedBuilder(
        animation: _bg,
        builder: (_, __) {
          final t = _bg.value;
          return Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.lerp(
                    const Alignment(-1, -1), const Alignment(1, 1), t)!,
                end: Alignment.lerp(
                    const Alignment(1, 1), const Alignment(-1, -1), t)!,
                colors: const [
                  Color(0xFF010409),
                  Color(0xFF0D1117),
                  Color(0xFF161B22),
                  Color(0xFF0D1117),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        _buildAnimatedBackground(),
        Scaffold(
          backgroundColor: Colors.transparent,
          body: SafeArea(child: widget.body),
          bottomNavigationBar: widget.bottomNavigationBar != null
              ? SafeArea(child: widget.bottomNavigationBar!)
              : null,
        ),
      ],
    );
  }
}

/// ------------------------------------------------------------
/// GLASS CARD
/// ------------------------------------------------------------
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  final VoidCallback? onTap;
  final Color? borderColor;

  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.onTap,
    this.borderColor,
  });

  @override
  Widget build(BuildContext context) {
    final content = ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: AppColors.cardBg.withOpacity(0.9),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: borderColor ?? Colors.white.withOpacity(0.08),
            ),
          ),
          child: child,
        ),
      ),
    );

    return onTap != null ? GestureDetector(onTap: onTap, child: content) : content;
  }
}

/// ------------------------------------------------------------
/// GLASS INPUT (FIX: this MUST exist for AuthScreen)
/// ------------------------------------------------------------
class GlassInput extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final IconData icon;
  final bool obscure;

  const GlassInput({
    super.key,
    required this.controller,
    required this.label,
    required this.icon,
    this.obscure = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: AppColors.cardBg.withOpacity(0.8),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white12),
      ),
      child: TextField(
        controller: controller,
        obscureText: obscure,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          icon: Icon(icon, color: Colors.white60),
          labelText: label,
          labelStyle: const TextStyle(color: Colors.white70),
          border: InputBorder.none,
        ),
      ),
    );
  }
}

/// ------------------------------------------------------------
/// GLASS TEXT FIELD
/// ------------------------------------------------------------
class GlassTextField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final bool readOnly;
  final TextInputType? keyboardType;

  const GlassTextField({
    super.key,
    required this.controller,
    required this.label,
    this.readOnly = false,
    this.keyboardType,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.cardBg.withOpacity(readOnly ? 0.6 : 0.85),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: TextField(
        controller: controller,
        readOnly: readOnly,
        keyboardType: keyboardType,
        style: TextStyle(color: readOnly ? AppColors.textGrey : Colors.white),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: TextStyle(color: readOnly ? AppColors.textGrey : Colors.white70),
          border: InputBorder.none,
        ),
      ),
    );
  }
}

/// ------------------------------------------------------------
/// NEON BUTTON
/// ------------------------------------------------------------
class NeonButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final Color color;

  const NeonButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.color = AppColors.accentBlue,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        elevation: 8,
      ),
      onPressed: onPressed,
      child: Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
    );
  }
}

/// ------------------------------------------------------------
/// STATUS METRIC
/// ------------------------------------------------------------
class StatusMetric extends StatelessWidget {
  final String label;
  final String value;
  final Color? color;

  const StatusMetric({
    super.key,
    required this.label,
    required this.value,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          label.toUpperCase(),
          style: const TextStyle(
            fontSize: 9,
            color: AppColors.textGrey,
            fontWeight: FontWeight.bold,
            letterSpacing: 1.2,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color ?? Colors.white,
          ),
        ),
      ],
    );
  }
}

/// ------------------------------------------------------------
/// SLIDE FADE IN ANIMATION
/// ------------------------------------------------------------
class SlideFadeIn extends StatefulWidget {
  final Widget child;
  final Duration duration;
  final Duration delay;
  final double offsetY;

  const SlideFadeIn({
    super.key,
    required this.child,
    this.duration = const Duration(milliseconds: 500),
    this.delay = Duration.zero,
    this.offsetY = 20,
  });

  @override
  State<SlideFadeIn> createState() => _SlideFadeInState();
}

class _SlideFadeInState extends State<SlideFadeIn>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _opacity;
  late Animation<Offset> _slide;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: widget.duration,
    );

    _opacity = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );

    _slide = Tween<Offset>(
      begin: Offset(0, widget.offsetY / 100),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );

    Future.delayed(widget.delay, () {
      if (mounted) _controller.forward();
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _opacity,
      child: SlideTransition(
        position: _slide,
        child: widget.child,
      ),
    );
  }
}

