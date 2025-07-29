import { ThemeConfig } from 'antd';

// Dark theme configuration for Ant Design
// Inspired by your current Discord-style theme
export const antdDarkTheme: ThemeConfig = {
  algorithm: undefined, // We'll define custom dark colors
  token: {
    // Core color palette
    colorPrimary: '#5865f2', // Discord blue for primary actions
    colorSuccess: '#57f287', // Green for success states
    colorWarning: '#ffa500', // Orange for warnings
    colorError: '#ed4245', // Red for errors
    colorInfo: '#5865f2', // Primary blue for info

    // Background colors
    colorBgBase: '#1a1a1a', // Main background
    colorBgContainer: '#23272a', // Card/container background
    colorBgElevated: '#2f3136', // Elevated surface (modals, dropdowns)
    colorBgLayout: '#1a1a1a', // Layout background

    // Border colors
    colorBorder: '#40444b', // Default borders
    colorBorderSecondary: '#40444b', // Secondary borders

    // Text colors
    colorText: '#ffffff', // Primary text
    colorTextSecondary: '#b9bbbe', // Secondary text
    colorTextTertiary: '#72767d', // Tertiary text
    colorTextQuaternary: '#4f545c', // Quaternary text
    colorTextDescription: '#99aab5', // Description text

    // Component specific
    colorFillAlter: '#2f3136', // Alternative fill
    colorFillSecondary: '#40444b', // Secondary fill
    colorFillTertiary: '#4f545c', // Tertiary fill
    colorFillQuaternary: '#5d6269', // Quaternary fill

    // Typography
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    fontSize: 14,
    fontSizeHeading1: 30,
    fontSizeHeading2: 24,
    fontSizeHeading3: 20,
    fontSizeHeading4: 18,
    fontSizeHeading5: 16,

    // Layout
    borderRadius: 8,
    borderRadiusLG: 12,
    borderRadiusSM: 6,
    borderRadiusXS: 4,

    // Spacing
    padding: 20,
    paddingLG: 32,
    paddingSM: 16,
    paddingXS: 12,
    paddingXXS: 8,

    margin: 20,
    marginLG: 32,
    marginSM: 16,
    marginXS: 12,
    marginXXS: 8,

    // Control heights
    controlHeight: 40,
    controlHeightLG: 48,
    controlHeightSM: 32,
    controlHeightXS: 24,

    // Line height
    lineHeight: 1.5,
    lineHeightHeading1: 1.25,
    lineHeightHeading2: 1.3,
    lineHeightHeading3: 1.35,
    lineHeightHeading4: 1.4,
    lineHeightHeading5: 1.45,

    // Motion
    motionDurationFast: '0.1s',
    motionDurationMid: '0.2s',
    motionDurationSlow: '0.3s',
  },
  components: {
    // Layout components
    Layout: {
      bodyBg: '#1a1a1a',
      headerBg: '#23272a',
      headerHeight: 64,
      headerPadding: '0 24px',
      siderBg: '#23272a',
      triggerBg: '#40444b',
      triggerColor: '#ffffff',
    },

    // Menu
    Menu: {
      darkItemBg: '#23272a',
      darkItemColor: '#b9bbbe',
      darkItemHoverBg: '#40444b',
      darkItemHoverColor: '#ffffff',
      darkItemSelectedBg: '#5865f2',
      darkItemSelectedColor: '#ffffff',
      darkSubMenuItemBg: '#2f3136',
    },

    // Cards
    Card: {
      headerBg: '#23272a',
      actionsBg: '#2f3136',
      colorBgContainer: '#23272a',
      colorBorderSecondary: '#40444b',
    },

    // Buttons
    Button: {
      primaryShadow: 'none',
      defaultShadow: 'none',
      dangerShadow: 'none',
      colorText: '#ffffff',
      colorTextDisabled: '#72767d',
      colorBgContainerDisabled: '#40444b',
      borderColorDisabled: '#40444b',
    },

    // Forms
    Input: {
      colorBgContainer: '#40444b',
      colorBorder: '#72767d',
      colorText: '#ffffff',
      colorTextPlaceholder: '#72767d',
      colorBgContainerDisabled: '#2f3136',
      colorTextDisabled: '#72767d',
      activeBorderColor: '#5865f2',
      hoverBorderColor: '#7289da',
    },

    Select: {
      colorBgContainer: '#40444b',
      colorBgElevated: '#2f3136',
      colorBorder: '#72767d',
      colorText: '#ffffff',
      colorTextPlaceholder: '#72767d',
      optionSelectedBg: '#5865f2',
      optionActiveBg: '#40444b',
    },

    // Tabs
    Tabs: {
      cardBg: '#23272a',
      itemColor: '#99aab5',
      itemHoverColor: '#ffffff',
      itemSelectedColor: '#ffffff',
      inkBarColor: '#5865f2',
      itemActiveBg: '#40444b',
    },

    // Table
    Table: {
      headerBg: '#2f3136',
      headerColor: '#ffffff',
      rowHoverBg: '#40444b',
      colorBgContainer: '#23272a',
      borderColor: '#40444b',
    },

    // Modal
    Modal: {
      contentBg: '#2f3136',
      headerBg: '#23272a',
      footerBg: '#23272a',
      colorText: '#ffffff',
    },

    // Notification
    Notification: {
      colorBgElevated: '#2f3136',
      colorText: '#ffffff',
      colorTextHeading: '#ffffff',
    },

    // Message
    Message: {
      colorBgElevated: '#2f3136',
      colorText: '#ffffff',
    },

    // Slider
    Slider: {
      railBg: '#40444b',
      railHoverBg: '#4f545c',
      trackBg: '#5865f2',
      trackHoverBg: '#7289da',
      handleColor: '#5865f2',
      handleActiveColor: '#7289da',
      dotActiveBorderColor: '#5865f2',
    },

    // Switch
    Switch: {
      colorPrimary: '#5865f2',
      colorPrimaryHover: '#7289da',
      colorTextQuaternary: '#72767d',
      colorTextTertiary: '#99aab5',
    },

    // Progress
    Progress: {
      defaultColor: '#5865f2',
      remainingColor: '#40444b',
    },

    // Divider
    Divider: {
      colorSplit: '#40444b',
      colorText: '#99aab5',
    },

    // Tag
    Tag: {
      defaultBg: '#40444b',
      defaultColor: '#ffffff',
    },

    // Badge
    Badge: {
      colorBgContainer: '#ed4245',
      colorText: '#ffffff',
    },

    // Tooltip
    Tooltip: {
      colorBgSpotlight: '#2f3136',
      colorTextLightSolid: '#ffffff',
    },

    // Popover
    Popover: {
      colorBgElevated: '#2f3136',
      colorText: '#ffffff',
    },

    // Dropdown
    Dropdown: {
      colorBgElevated: '#2f3136',
      colorText: '#ffffff',
    },
  },
};

// Light theme fallback (in case you want to support theme switching)
export const antdLightTheme: ThemeConfig = {
  token: {
    colorPrimary: '#5865f2',
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
};
