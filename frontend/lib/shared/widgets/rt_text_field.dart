import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_typography.dart';

/// COMP-CORE-003: RTTextField grounded in Figma Hi-Fi Form Inputs
class RTTextField extends StatefulWidget {
  final String label;
  final String? hint;
  final TextEditingController controller;
  final String? Function(String?)? validator;
  final bool isPassword;
  final bool isRequired;
  final String? counterText;
  final String? helperText;
  final TextInputType keyboardType;
  final int maxLines;
  final bool isReadOnly;
  final Widget? prefixIcon;
  final Widget? suffixIcon;
  final void Function(String)? onChanged;

  const RTTextField({
    super.key,
    required this.label,
    this.hint,
    required this.controller,
    this.validator,
    this.isPassword = false,
    this.isRequired = false,
    this.counterText,
    this.helperText,
    this.keyboardType = TextInputType.text,
    this.maxLines = 1,
    this.isReadOnly = false,
    this.prefixIcon,
    this.suffixIcon,
    this.onChanged,
  });

  @override
  State<RTTextField> createState() => _RTTextFieldState();
}

class _RTTextFieldState extends State<RTTextField> {
  late bool _obscureText;

  @override
  void initState() {
    super.initState();
    _obscureText = widget.isPassword;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            RichText(
              text: TextSpan(
                text: widget.label,
                style: AppTypography.labelMedium.copyWith(
                  fontWeight: FontWeight.w700,
                  fontSize: 12.0,
                  color: AppColors.navyHeader,
                ),
                children: [
                  if (widget.isRequired)
                    const TextSpan(
                      text: ' *',
                      style: TextStyle(color: AppColors.error, fontWeight: FontWeight.bold),
                    ),
                ],
              ),
            ),
            if (widget.counterText != null)
              Text(
                widget.counterText!,
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSubtle,
                  fontSize: 11.0,
                ),
              ),
          ],
        ),
        const SizedBox(height: 6),
        TextFormField(
          controller: widget.controller,
          validator: widget.validator,
          obscureText: _obscureText,
          keyboardType: widget.keyboardType,
          maxLines: widget.isPassword ? 1 : widget.maxLines,
          readOnly: widget.isReadOnly,
          onChanged: widget.onChanged,
          style: AppTypography.bodyLarge.copyWith(
            color: AppColors.textSlate,
            fontWeight: FontWeight.w500,
          ),
          decoration: InputDecoration(
            hintText: widget.hint,
            filled: true,
            fillColor: Colors.white,
            prefixIcon: widget.prefixIcon,
            suffixIcon: widget.isPassword
                ? IconButton(
                    icon: Icon(
                      _obscureText ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                      color: AppColors.textSubtle,
                      size: 20,
                    ),
                    onPressed: () {
                      setState(() {
                        _obscureText = !_obscureText;
                      });
                    },
                  )
                : widget.suffixIcon,
            contentPadding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 12.0),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12.0),
              borderSide: const BorderSide(color: AppColors.borderSubtle, width: 1.0),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12.0),
              borderSide: const BorderSide(color: AppColors.borderSubtle, width: 1.0),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12.0),
              borderSide: const BorderSide(color: AppColors.primaryAction, width: 1.5),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12.0),
              borderSide: const BorderSide(color: AppColors.error, width: 1.0),
            ),
          ),
        ),
        if (widget.helperText != null) ...[
          const SizedBox(height: 4),
          Text(
            widget.helperText!,
            style: AppTypography.caption.copyWith(
              color: AppColors.textSubtle,
              fontSize: 11.0,
            ),
          ),
        ],
      ],
    );
  }
}
