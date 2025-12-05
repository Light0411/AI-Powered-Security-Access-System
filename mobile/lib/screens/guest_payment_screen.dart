import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../state/client_state.dart';
import '../widgets/ui_kit.dart';


class GuestPaymentScreen extends StatefulWidget {
  const GuestPaymentScreen({super.key});

  @override
  State<GuestPaymentScreen> createState() => _GuestPaymentScreenState();
}

class _GuestPaymentScreenState extends State<GuestPaymentScreen> {
  final _plate = TextEditingController();
  String source = 'touchngo';

  @override
  Widget build(BuildContext context) {
    final state = context.watch<ClientState>();
    final lookup = state.guestLookup;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          const SizedBox(height: 20),
          const Icon(Icons.payments_rounded, size: 48, color: AppColors.accentPurple),
          const SizedBox(height: 16),
          const Text(
            'Guest Checkout',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Enter plate number to pay for parking',
            style: TextStyle(color: AppColors.textGrey),
          ),
          const SizedBox(height: 32),

          // --- Plate Input ---
          GlassCard(
            child: Column(
              children: [
                TextField(
                  controller: _plate,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 28, 
                    fontWeight: FontWeight.bold, 
                    letterSpacing: 4,
                    fontFamily: 'monospace'
                  ),
                  textCapitalization: TextCapitalization.characters,
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    hintText: 'ABC1234',
                    hintStyle: TextStyle(color: Colors.white10),
                  ),
                ),
                Container(height: 2, width: 100, color: AppColors.accentPurple),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: NeonButton(
                    label: "Check Balance",
                    color: AppColors.accentPurple,
                    onPressed: () => state.lookupGuest(
                      plateText: _plate.text.trim().toUpperCase(),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // --- Result Overlay ---
          if (lookup != null) ...[
            const SizedBox(height: 32),
            SlideFadeIn(
              child: Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    colors: [AppColors.accentBlue.withOpacity(0.2), AppColors.accentPurple.withOpacity(0.2)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  border: Border.all(color: Colors.white.withOpacity(0.2)),
                ),
                child: Column(
                  children: [
                    const Text('TOTAL DUE', style: TextStyle(fontSize: 10, letterSpacing: 2, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text(
                      'RM${lookup.amountDue.toStringAsFixed(2)}',
                      style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const SizedBox(height: 4),
                    Text(lookup.session.status.toUpperCase(), style: const TextStyle(color: AppColors.accentGreen, fontSize: 12, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 32),
            
            // Payment Source Dropdown stylized
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: source,
                  dropdownColor: AppColors.cardBg,
                  isExpanded: true,
                  style: const TextStyle(color: Colors.white),
                  items: const [
                    DropdownMenuItem(value: 'touchngo', child: Text('Touch \'n Go eWallet')),
                    DropdownMenuItem(value: 'wallet', child: Text('Wallet Credits')),
                  ],
                  onChanged: (value) => setState(() => source = value!),
                ),
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: NeonButton(
                label: "Confirm Payment",
                color: AppColors.accentGreen,
                onPressed: state.isBusy ? null : () => state.payGuest(paymentSource: source),
              ),
            ),
          ],
          
          if (state.lastPayment != null)
             Padding(
               padding: const EdgeInsets.only(top: 24.0),
               child: SlideFadeIn(
                 child: Container(
                   padding: const EdgeInsets.all(12),
                   decoration: BoxDecoration(
                     color: AppColors.accentGreen.withOpacity(0.1),
                     borderRadius: BorderRadius.circular(12),
                     border: Border.all(color: AppColors.accentGreen.withOpacity(0.3))
                   ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.check_circle, color: AppColors.accentGreen),
                      SizedBox(width: 8),
                      Text("Payment Successful", style: TextStyle(color: AppColors.accentGreen, fontWeight: FontWeight.bold)),
                    ],
                  ),
                 ),
               ),
             )
        ],
      ),
    );
  }
}
