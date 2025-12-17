import 'package:flutter/material.dart';

class PenguinLoader extends StatefulWidget {
  final double size;

  const PenguinLoader({super.key, this.size = 50.0});

  @override
  State<PenguinLoader> createState() => _PenguinLoaderState();
}

class _PenguinLoaderState extends State<PenguinLoader>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return RotationTransition(
      turns: _controller,
      child: Text(
        '🐧', // Penguin emoji
        style: TextStyle(fontSize: widget.size),
      ),
    );
  }
}
