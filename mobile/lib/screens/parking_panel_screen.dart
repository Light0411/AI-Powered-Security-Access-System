import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../state/client_state.dart';
import '../widgets/ui_kit.dart';

class ParkingPanelScreen extends StatelessWidget {
  const ParkingPanelScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<ClientState>();
    final overview = state.parking;

    return RefreshIndicator(
      onRefresh: () => context.read<ClientState>().refreshParking(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'LIVE AVAILABILITY',
            style: TextStyle(color: AppColors.textGrey, fontSize: 10, letterSpacing: 2, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          if (overview == null)
            const Center(child: CircularProgressIndicator())
          else
            ...overview.venues.map(
              (venue) => Padding(
                padding: const EdgeInsets.only(bottom: 12.0),
                child: SlideFadeIn(child: _VenueCard(venue: venue)),
              ),
            ),
        ],
      ),
    );
  }
}

class _VenueCard extends StatelessWidget {
  final ParkingVenue venue;
  const _VenueCard({required this.venue});

  @override
  Widget build(BuildContext context) {
    final percent = venue.percent.clamp(0, 100);
    final isHigh = percent > 90;
    final color = isHigh ? Colors.redAccent : (percent > 70 ? Colors.amber : AppColors.accentGreen);

    return GlassCard(
      padding: const EdgeInsets.all(20),
      borderColor: color.withOpacity(0.3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(venue.name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              Text('${venue.occupied}/${venue.capacity}',
                  style: TextStyle(fontSize: 14, color: color, fontWeight: FontWeight.w600)),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: percent / 100,
                    minHeight: 6,
                    backgroundColor: Colors.white10,
                    color: color,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text('${percent.toStringAsFixed(0)}%', style: TextStyle(fontWeight: FontWeight.bold, color: color)),
            ],
          ),
          const SizedBox(height: 8),
          Text('${venue.capacity - venue.occupied} spots remaining',
              style: const TextStyle(fontSize: 12, color: Colors.white70)),
        ],
      ),
    );
  }
}
