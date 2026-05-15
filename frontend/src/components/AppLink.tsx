import React from 'react';
import { Link, LinkProps } from 'react-router-dom';
import { withAppId } from '@/utils/appParam';

/**
 * A wrapper around react-router-dom Link that automatically preserves 
 * the Semicolons 'app' query parameter in the target URL.
 */
export const AppLink: React.FC<LinkProps> = ({ to, ...props }) => {
  const finalTo = typeof to === 'string' ? withAppId(to) : to;
  // If 'to' is an object (Route location descriptor), we'd need to handle that too 
  // but most of our app uses strings.
  
  return <Link {...props} to={finalTo} />;
};
