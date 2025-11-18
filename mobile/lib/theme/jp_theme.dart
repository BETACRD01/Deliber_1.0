// lib/theme/jp_theme.dart

import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';

// ══════════════════════════════════════════════════════════════════════════════
// 🎨 COLORES JP EXPRESS
// ══════════════════════════════════════════════════════════════════════════════

class JPColors {
  // Colores principales
  static const primary = Color(0xFF0cb7f2); // Azul
  static const secondary = Color(0xFFFF7B00); // Naranja

  static const accent = Color(0xFFFFB800); // Amarillo
  // Fondos
  static const background = Color(0xFFF5F7FA);
  static const cardBg = Colors.white;
  static const surface = Colors.white; // ✅ AGREGADO
  static const overlayBg = Color(0x80000000);

  // Textos
  static const textPrimary = Color(0xFF2D3748);
  static const textSecondary = Color(0xFF718096);
  static const textHint = Color(0xFFA0AEC0);

  // Estados
  static const success = Color(0xFF48BB78);
  static const warning = Color(0xFFED8936);
  static const error = Color(0xFFF56565);
  static const info = Color(0xFF4299E1);

  // Gradientes
  static const primaryGradient = LinearGradient(
    colors: [Color(0xFF0cb7f2), Color(0xFF0891C7)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const secondaryGradient = LinearGradient(
    colors: [Color(0xFFFF7B00), Color(0xFFFF9500)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// 📝 ESTILOS DE TEXTO
// ══════════════════════════════════════════════════════════════════════════════

class JPTextStyles {
  static const h1 = TextStyle(
    fontSize: 28,
    fontWeight: FontWeight.bold,
    color: JPColors.textPrimary,
    letterSpacing: -0.5,
  );

  static const h2 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
    color: JPColors.textPrimary,
  );

  static const h3 = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w600,
    color: JPColors.textPrimary,
  );

  static const body = TextStyle(fontSize: 16, color: JPColors.textPrimary);

  static const bodySecondary = TextStyle(
    fontSize: 16,
    color: JPColors.textSecondary,
  );

  static const caption = TextStyle(fontSize: 14, color: JPColors.textSecondary);

  static const small = TextStyle(fontSize: 12, color: JPColors.textHint);
  // NUEVOS ESTILOS — h4, h5, h6
  static const h4 = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w600,
    color: JPColors.textPrimary,
  );

  static const h5 = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w600,
    color: JPColors.textPrimary,
  );

  static const h6 = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w600,
    color: JPColors.textPrimary,
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// 🎨 TEMA COMPLETO
// ══════════════════════════════════════════════════════════════════════════════

class JPTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: JPColors.primary,
        primary: JPColors.primary,
        secondary: JPColors.secondary,
        surface: JPColors.background,
      ),
      scaffoldBackgroundColor: JPColors.background,
      appBarTheme: const AppBarTheme(
        backgroundColor: JPColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
      ),
      cardTheme: CardThemeData(
        color: JPColors.cardBg,
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: JPColors.secondary,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: JPColors.secondary,
        foregroundColor: Colors.white,
      ),
    );
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// 🧩 WIDGETS COMPARTIDOS
// ══════════════════════════════════════════════════════════════════════════════

/// Avatar personalizado con borde JP
class JPAvatar extends StatelessWidget {
  final String? imageUrl;
  final double radius;
  final bool showEditIcon;
  final VoidCallback? onTap;

  const JPAvatar({
    super.key,
    this.imageUrl,
    this.radius = 40,
    this.showEditIcon = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Stack(
        children: [
          // Avatar circular
          Container(
            width: radius * 2,
            height: radius * 2,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 3),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withAlpha(51),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: ClipOval(child: _buildImage()),
          ),

          // Ícono de editar (opcional)
          if (showEditIcon)
            Positioned(
              bottom: 0,
              right: 0,
              child: Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: JPColors.primary,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 2),
                ),
                child: Icon(
                  Icons.camera_alt,
                  size: radius * 0.35,
                  color: Colors.white,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildImage() {
    if (imageUrl == null || imageUrl!.isEmpty) {
      // Avatar por defecto
      return Container(
        color: JPColors.primary.withValues(alpha: 0.1),
        child: Icon(Icons.person, size: radius * 1.2, color: JPColors.primary),
      );
    }

    // Imagen con caché para mejor rendimiento
    return CachedNetworkImage(
      imageUrl: imageUrl!,
      fit: BoxFit.cover,
      placeholder: (context, url) => Center(
        child: CircularProgressIndicator(
          strokeWidth: 2,
          valueColor: const AlwaysStoppedAnimation<Color>(JPColors.primary),
        ),
      ),
      errorWidget: (context, url, error) => Container(
        color: JPColors.error.withValues(alpha: 0.1),
        child: Icon(Icons.person, size: radius * 1.2, color: JPColors.error),
      ),
    );
  }
}

/// Loading personalizado
class JPLoading extends StatelessWidget {
  final String? message;

  const JPLoading({super.key, this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(color: JPColors.primary),
          if (message != null) ...[
            const SizedBox(height: 16),
            Text(message!, style: JPTextStyles.bodySecondary),
          ],
        ],
      ),
    );
  }
}

/// Snackbar personalizado
class JPSnackbar {
  static void show(
    BuildContext context,
    String message, {
    bool isError = false,
    Duration duration = const Duration(seconds: 3),
  }) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              isError ? Icons.error_outline : Icons.check_circle_outline,
              color: Colors.white,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(color: Colors.white, fontSize: 14),
              ),
            ),
          ],
        ),
        backgroundColor: isError ? JPColors.error : JPColors.success,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        duration: duration,
      ),
    );
  }

  // ✅ NUEVO: Método success
  static void success(BuildContext context, String message) {
    show(context, message, isError: false);
  }

  // ✅ NUEVO: Método error
  static void error(BuildContext context, String message) {
    show(context, message, isError: true);
  }

  // ✅ NUEVO: Método info
  static void info(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.info_outline, color: Colors.white),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(color: Colors.white, fontSize: 14),
              ),
            ),
          ],
        ),
        backgroundColor: JPColors.info,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        duration: const Duration(seconds: 3),
      ),
    );
  }
}

/// Estado vacío
class JPEmptyState extends StatelessWidget {
  final IconData icon;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  const JPEmptyState({
    super.key,
    required this.icon,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 80, color: JPColors.textHint),
            const SizedBox(height: 16),
            Text(
              message,
              style: JPTextStyles.body.copyWith(color: JPColors.textSecondary),
              textAlign: TextAlign.center,
            ),
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: onAction,
                icon: const Icon(Icons.add),
                label: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Card con sombra JP
class JPCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;
  final VoidCallback? onTap;

  const JPCard({super.key, required this.child, this.padding, this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: padding ?? const EdgeInsets.all(16),
          child: child,
        ),
      ),
    );
  }
}

/// Badge de nivel
class JPBadge extends StatelessWidget {
  final String label;
  final Color color;
  final IconData? icon;

  const JPBadge({
    super.key,
    required this.label,
    required this.color,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color, width: 1.5),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 16, color: color),
            const SizedBox(width: 4),
          ],
          Text(
            label,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

/// Skeleton loading
class JPSkeleton extends StatefulWidget {
  final double width;
  final double height;
  final BorderRadius? borderRadius;

  const JPSkeleton({
    super.key,
    required this.width,
    required this.height,
    this.borderRadius,
  });

  @override
  State<JPSkeleton> createState() => _JPSkeletonState();
}

class _JPSkeletonState extends State<JPSkeleton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(
            borderRadius: widget.borderRadius ?? BorderRadius.circular(8),
            gradient: LinearGradient(
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
              colors: [Colors.grey[300]!, Colors.grey[100]!, Colors.grey[300]!],
              stops: [
                _controller.value - 0.3,
                _controller.value,
                _controller.value + 0.3,
              ].map((e) => e.clamp(0.0, 1.0)).toList(),
            ),
          ),
        );
      },
    );
  }
}
