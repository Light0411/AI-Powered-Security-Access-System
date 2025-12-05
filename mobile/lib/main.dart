import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import 'screens/auth_screen.dart';
import 'screens/home_shell.dart';
import 'state/client_state.dart';
import 'widgets/ui_kit.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  // FORCE status bar to be light (for dark backgrounds)
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light, 
    systemNavigationBarColor: Color(0xFF0F172A),
    systemNavigationBarIconBrightness: Brightness.light,
  ));
  
  runApp(const SmartGateApp());
}

class SmartGateApp extends StatelessWidget {
  const SmartGateApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => ClientState(),
      child: Consumer<ClientState>(
        builder: (context, state, _) {
          return MaterialApp(
            title: 'ParkFlow Client',
            debugShowCheckedModeBanner: false,
            // FORCE DARK MODE
            themeMode: ThemeMode.dark,
            theme: ThemeData.dark(useMaterial3: true).copyWith(
              scaffoldBackgroundColor: AppColors.bgDark, // Deep Navy Background
              primaryColor: AppColors.accentGreen,
              colorScheme: const ColorScheme.dark(
                primary: AppColors.accentGreen,
                secondary: AppColors.accentBlue,
                surface: AppColors.bgLight,
                background: AppColors.bgDark,
              ),
              // Default text style to white
              textTheme: Typography.whiteMountainView.apply(
                fontFamily: 'Inter', 
                bodyColor: Colors.white,
                displayColor: Colors.white,
              ),
            ),
            home: state.isAuthenticated ? const HomeShell() : const AuthScreen(),
          );
        },
      ),
    );
  }
}
